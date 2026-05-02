# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""The eight company archetypes.

Each archetype is a dictionary of feature → weight. The scorer projects
a company's extracted feature vector onto each archetype to get a per-
archetype score for the company. Then it compares against the candidate's
chosen archetypes (with weights) to produce an overall fit score.

Tunability: numbers here are deliberately conservative defaults. Inter-rater
calibration (Section 15 of the design doc) drives ongoing tuning.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Archetype:
    name: str
    display_name: str
    description: str
    weights: dict[str, float]
    """Feature → weight. Weights can be negative (penalty)."""


# Canonical features (must match the keys produced by features.py extraction).
# Each feature has a "high-end" and "low-end" mapping; the scorer interprets
# values like "small / mid / large / enterprise" via FEATURE_VALUE_MAP.
FEATURE_VALUE_MAP: dict[str, dict[str, float]] = {
    "headcount_estimate": {"small": 1.0, "mid": 0.65, "large": 0.30, "enterprise": 0.0, "null": 0.5},
    "funding_stage": {"seed": 1.0, "series_a": 0.85, "series_b": 0.65, "series_c": 0.40, "public": 0.0, "null": 0.5},
    "remote_policy": {"remote_first": 1.0, "hybrid": 0.5, "in_office": 0.0, "flexible": 0.7, "null": 0.5},
    "travel_pct": {"0": 0.0, "low": 0.25, "moderate": 0.6, "high": 1.0, "null": 0.3},
    "mission_concreteness": {"low": 0.0, "moderate": 0.5, "high": 1.0, "null": 0.3},
    "ic_track_signal": {"weak": 0.0, "moderate": 0.5, "strong": 1.0, "null": 0.3},
}


# ---------------------------------------------------------------------------
# Archetype definitions
# ---------------------------------------------------------------------------

ARCHETYPES: dict[str, Archetype] = {
    "founder_track": Archetype(
        name="founder_track",
        display_name="The Founder Track",
        description="Fresh grads, aspiring founders, and early-career builders who want range and pace.",
        weights={
            "headcount_small_or_mid": 1.0,
            "funding_early_stage": 0.9,
            "ic_track_signal": -0.2,  # too much specialization is the wrong signal
            "wlb_score_high": -0.3,   # founders don't optimize for WLB
        },
    ),
    "corporate_climber": Archetype(
        name="corporate_climber",
        display_name="The Corporate Climber",
        description="Mid-career, ambition for title and scope. Wants ladders and structured promotion.",
        weights={
            "headcount_large_or_enterprise": 1.0,
            "funding_late_stage_or_public": 0.8,
            "ic_track_signal": 0.4,  # leveling structure helps
        },
    ),
    "stable_provider": Archetype(
        name="stable_provider",
        display_name="The Stable Provider",
        description="Mid-career, family-focused. Values predictability, benefits, work-life balance.",
        weights={
            "wlb_score_high": 1.0,
            "parental_leave_generous": 0.9,
            "headcount_large_or_enterprise": 0.4,
            "funding_late_stage_or_public": 0.4,
            "remote_or_flexible": 0.3,
        },
    ),
    "women_forward": Archetype(
        name="women_forward",
        display_name="The Women-Forward Workplace",
        description="Women prioritizing cultures with female leadership and lived equity.",
        weights={
            "women_leadership_high": 1.0,
            "parental_leave_generous": 0.7,
            "wlb_score_high": 0.4,
        },
    ),
    "globe_trotter": Archetype(
        name="globe_trotter",
        display_name="The Globe-Trotter",
        description="People who love travel as part of the job.",
        weights={
            "travel_pct": 1.0,  # interpreted via FEATURE_VALUE_MAP
        },
    ),
    "mission_believer": Archetype(
        name="mission_believer",
        display_name="The Mission Believer",
        description="People who need the work itself to matter.",
        weights={
            "mission_concreteness": 1.0,
        },
    ),
    "deep_specialist": Archetype(
        name="deep_specialist",
        display_name="The Deep Specialist",
        description="Senior ICs who want technical depth and respect.",
        weights={
            "ic_track_signal": 1.0,
            "headcount_large_or_enterprise": 0.4,
        },
    ),
    "remote_first": Archetype(
        name="remote_first",
        display_name="The Remote-First Lifer",
        description="Async-friendly, distributed, no return-to-office whiplash.",
        weights={
            "remote_first_explicit": 1.0,
            "remote_or_flexible": 0.6,
        },
    ),
}


# ---------------------------------------------------------------------------
# Synthetic feature derivation
# ---------------------------------------------------------------------------

def derive_synthetic_features(features: dict) -> dict[str, float]:
    """Convert raw extracted features into the synthetic features that
    archetype weights reference (e.g. headcount_small_or_mid).
    """
    synth: dict[str, float] = {}

    hc = (features.get("headcount_estimate") or "null").lower()
    synth["headcount_small_or_mid"] = 1.0 if hc in ("small", "mid") else 0.0
    synth["headcount_large_or_enterprise"] = 1.0 if hc in ("large", "enterprise") else 0.0

    fs = (features.get("funding_stage") or "null").lower()
    synth["funding_early_stage"] = 1.0 if fs in ("seed", "series_a", "series_b") else 0.0
    synth["funding_late_stage_or_public"] = 1.0 if fs in ("series_c", "public") else 0.0

    wlb = features.get("wlb_score")
    if isinstance(wlb, (int, float)):
        synth["wlb_score_high"] = max(0.0, min(1.0, (wlb - 3.0) / 1.5))  # 3.0→0, 4.5→1
    else:
        synth["wlb_score_high"] = 0.5

    pl = features.get("parental_leave_weeks")
    if isinstance(pl, (int, float)):
        synth["parental_leave_generous"] = max(0.0, min(1.0, (pl - 6) / 14))  # 6→0, 20→1
    else:
        synth["parental_leave_generous"] = 0.3

    wl = features.get("women_in_named_leadership_pct")
    if isinstance(wl, (int, float)):
        synth["women_leadership_high"] = max(0.0, min(1.0, (wl - 0.15) / 0.30))  # 15%→0, 45%→1
    else:
        synth["women_leadership_high"] = 0.3

    rp = (features.get("remote_policy") or "null").lower()
    synth["remote_first_explicit"] = 1.0 if rp == "remote_first" else 0.0
    synth["remote_or_flexible"] = 1.0 if rp in ("remote_first", "flexible") else (0.5 if rp == "hybrid" else 0.0)

    # Pass-through normalized features
    for k in ("travel_pct", "mission_concreteness", "ic_track_signal"):
        v = features.get(k)
        if isinstance(v, str) and v.lower() in FEATURE_VALUE_MAP.get(k, {}):
            synth[k] = FEATURE_VALUE_MAP[k][v.lower()]
        else:
            synth[k] = FEATURE_VALUE_MAP.get(k, {}).get("null", 0.3)

    return synth


def score_company_against_archetype(synthetic: dict[str, float], archetype: Archetype) -> float:
    """Returns a score in [0, 1] for how well the company matches the archetype."""
    total_pos_weight = sum(w for w in archetype.weights.values() if w > 0)
    if total_pos_weight == 0:
        return 0.0

    raw = 0.0
    for feature, weight in archetype.weights.items():
        val = synthetic.get(feature, 0.0)
        raw += val * weight

    # Normalize: positive weights cap the score; negatives can push down
    score = raw / total_pos_weight
    return max(0.0, min(1.0, score))
