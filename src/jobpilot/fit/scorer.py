# ============================================================================
# Copyright (c) 2026 Areej Ahmed. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""The fit-scoring orchestrator.

Pipeline:
  1. Resolve company from job URL
  2. Pull JD text (always — we have the URL)
  3. Pull Glassdoor data + careers page (cached, best-effort)
  4. LLM extracts structured features from raw sources
  5. Convert features → synthetic features → per-archetype score for the company
  6. Compute candidate fit as weighted overlap with their selected archetypes
  7. LLM writes a one-paragraph reasoning that cites concrete evidence
"""
from __future__ import annotations

import json
from typing import Any

from jobpilot.api.schemas import CandidateArchetype, Evidence, ScoreResponse
from jobpilot.fit.archetypes import (
    ARCHETYPES,
    derive_synthetic_features,
    score_company_against_archetype,
)
from jobpilot.fit.scrapers.careers import fetch_careers_page
from jobpilot.fit.scrapers.glassdoor import fetch_glassdoor
from jobpilot.fit.scrapers.greenhouse_jd import scrape_jd
from jobpilot.llm.client import get_client
from jobpilot.llm.prompts import feature_extraction_prompt, reasoning_prompt


async def score_job(job_url: str, candidate_archetypes: list[CandidateArchetype]) -> ScoreResponse:
    """Run the full scoring pipeline. Always returns a ScoreResponse — never raises."""
    if not candidate_archetypes:
        return ScoreResponse(
            status="failed",
            fit_score=0.0,
            verdict="uncertain",
            error="no candidate_archetypes provided",
        )

    # 1-2: company + JD
    try:
        company, jd_text = await scrape_jd(job_url)
    except Exception as e:
        return ScoreResponse(
            status="failed",
            fit_score=0.0,
            verdict="uncertain",
            error=f"JD scrape failed: {e}",
        )

    # 3: best-effort enrichment
    glassdoor, gd_age = await fetch_glassdoor(company)
    careers, careers_age = await fetch_careers_page(company)

    # 4: LLM feature extraction
    llm = get_client()
    scores_summary = {
        k: v for k, v in glassdoor.items()
        if k in ("overall_rating", "wlb_score", "culture_score") and v is not None
    }
    system, user = feature_extraction_prompt(
        jd_text=jd_text,
        careers_text=careers.get("text", ""),
        reviews_text=glassdoor.get("reviews_sample", ""),
        scores_json=json.dumps(scores_summary),
    )
    try:
        features = await llm.complete_json(system, user, max_tokens=900)
    except Exception:
        # Degrade gracefully: empty feature dict means most archetype scores → 0
        features = {}

    # 5: synthetic features + per-archetype scores
    synthetic = derive_synthetic_features(features)
    archetype_scores = {
        name: round(score_company_against_archetype(synthetic, arch), 3)
        for name, arch in ARCHETYPES.items()
    }

    # 6: candidate fit = weighted dot of candidate weights against company scores
    total_w = sum(ca.weight for ca in candidate_archetypes) or 1.0
    fit_score = 0.0
    for ca in candidate_archetypes:
        company_score = archetype_scores.get(ca.name, 0.0)
        fit_score += (ca.weight / total_w) * company_score
    fit_score = round(max(0.0, min(1.0, fit_score)), 3)

    # 7: reasoning
    sorted_cas = sorted(candidate_archetypes, key=lambda c: -c.weight)
    primary = sorted_cas[0]
    secondary = sorted_cas[1] if len(sorted_cas) > 1 else CandidateArchetype(name=primary.name, weight=0.0)

    try:
        sys2, user2 = reasoning_prompt(
            primary_archetype=primary.name,
            primary_weight=primary.weight,
            secondary_archetype=secondary.name,
            secondary_weight=secondary.weight,
            company_name=company,
            features_json=json.dumps(features),
            archetype_scores_json=json.dumps(archetype_scores),
            fit_score=fit_score,
        )
        reasoning = await llm.complete(sys2, user2, max_tokens=300)
    except Exception:
        reasoning = "Reasoning unavailable (LLM error). Score is based on extracted features only."

    # Verdict thresholds
    if fit_score >= 0.65:
        verdict = "apply"
    elif fit_score >= 0.45:
        verdict = "uncertain"
    else:
        verdict = "skip"

    # Evidence list — pulled from the LLM's evidence field if present
    evidence_list: list[Evidence] = []
    raw_evidence = features.get("evidence") if isinstance(features, dict) else None
    if isinstance(raw_evidence, list):
        for e in raw_evidence[:8]:
            if isinstance(e, dict) and "claim" in e:
                evidence_list.append(Evidence(
                    source=str(e.get("source", "unknown")),
                    claim=str(e.get("claim", "")),
                    url=careers.get("url") if e.get("source") == "careers" else None,
                ))

    return ScoreResponse(
        status="scored",
        company=company,
        fit_score=fit_score,
        verdict=verdict,  # type: ignore[arg-type]
        company_archetype_scores=archetype_scores,
        reasoning=reasoning.strip(),
        evidence=evidence_list,
        cache_age_days=max(gd_age or 0, careers_age or 0),
    )
