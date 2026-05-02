# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Prompt templates. Versioned in code so changes are reviewable."""
from __future__ import annotations


OPEN_QUESTION_SYSTEM = """\
You are helping a real candidate write a real answer for a real job
application. Write in their voice, in the first person. Do not pretend
to be them — be the writer they would be if they had thirty quiet
minutes and the resume in front of them.

Hard rules:
- No clichés ("I'm thrilled", "deeply passionate", "leverage", "synergy").
- No three-part lists in every paragraph. Vary structure.
- Reference specific items from the resume, not generalities.
- Stay under {max_chars} characters and aim for 60-80% of that.
- Do not invent experience the resume does not support.
- No em-dashes used as a stylistic tic.

Output only the answer text. No preamble, no quotes, no markdown.
"""


OPEN_QUESTION_USER = """\
CANDIDATE RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

QUESTION (max {max_chars} characters):
{question_text}
"""


ARCHETYPE_FEATURE_SYSTEM = """\
You are extracting structured features from company data for an archetype-
matching system. Be conservative. If a feature is not directly evidenced
by the source material, return null. Do not extrapolate or guess.

Output a single JSON object matching the requested schema. No prose.
"""


ARCHETYPE_FEATURE_USER = """\
SOURCES:
- Greenhouse JD: {jd_text}
- Careers page: {careers_text}
- Glassdoor reviews (sampled): {reviews_text}
- Glassdoor numeric scores: {scores_json}

Extract these features as JSON. Use null for any feature not directly
evidenced.

{{
  "headcount_estimate": "small | mid | large | enterprise | null",
  "funding_stage": "seed | series_a | series_b | series_c | public | null",
  "remote_policy": "remote_first | hybrid | in_office | flexible | null",
  "travel_pct": "0 | low | moderate | high | null",
  "parental_leave_weeks": "<int or null>",
  "women_in_named_leadership_pct": "<float 0-1 or null>",
  "wlb_score": "<float 0-5 or null>",
  "mission_concreteness": "low | moderate | high | null",
  "ic_track_signal": "weak | moderate | strong | null",
  "evidence": [
    {{"feature": "<name>", "claim": "<short quote or paraphrase>", "source": "jd|careers|reviews|scores"}}
  ]
}}
"""


ARCHETYPE_REASONING_SYSTEM = """\
Given a company's extracted features and a candidate's archetype profile,
write one paragraph explaining the fit score. Cite at least three pieces
of concrete evidence from the features. No marketing language. No more
than 120 words. Output only the paragraph text.
"""


ARCHETYPE_REASONING_USER = """\
CANDIDATE PROFILE:
Primary archetype: {primary_archetype} (weight {primary_weight})
Secondary archetype: {secondary_archetype} (weight {secondary_weight})

COMPANY: {company_name}
EXTRACTED FEATURES: {features_json}
PER-ARCHETYPE SCORES: {archetype_scores_json}
OVERALL FIT SCORE: {fit_score}
"""


def open_question_prompt(*, resume_text: str, jd_text: str, question_text: str, max_chars: int) -> tuple[str, str]:
    system = OPEN_QUESTION_SYSTEM.format(max_chars=max_chars)
    user = OPEN_QUESTION_USER.format(
        resume_text=_truncate(resume_text, 4000),
        jd_text=_truncate(jd_text, 3000),
        max_chars=max_chars,
        question_text=question_text,
    )
    return system, user


def feature_extraction_prompt(*, jd_text: str, careers_text: str, reviews_text: str, scores_json: str) -> tuple[str, str]:
    return ARCHETYPE_FEATURE_SYSTEM, ARCHETYPE_FEATURE_USER.format(
        jd_text=_truncate(jd_text, 3000),
        careers_text=_truncate(careers_text, 3000),
        reviews_text=_truncate(reviews_text, 4000),
        scores_json=scores_json,
    )


def reasoning_prompt(*, primary_archetype: str, primary_weight: float,
                     secondary_archetype: str, secondary_weight: float,
                     company_name: str, features_json: str,
                     archetype_scores_json: str, fit_score: float) -> tuple[str, str]:
    return ARCHETYPE_REASONING_SYSTEM, ARCHETYPE_REASONING_USER.format(
        primary_archetype=primary_archetype,
        primary_weight=primary_weight,
        secondary_archetype=secondary_archetype,
        secondary_weight=secondary_weight,
        company_name=company_name,
        features_json=features_json,
        archetype_scores_json=archetype_scores_json,
        fit_score=fit_score,
    )


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 50] + "\n...[truncated]..."
