# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Unit tests for the form parser and honeypot detector.

These tests use synthetic HTML rather than recorded Greenhouse pages,
so they run without a browser.
"""
from __future__ import annotations

import pytest

from jobpilot.fit.archetypes import (
    ARCHETYPES,
    derive_synthetic_features,
    score_company_against_archetype,
)


class TestArchetypes:
    def test_all_archetypes_present(self) -> None:
        names = set(ARCHETYPES.keys())
        expected = {
            "founder_track",
            "corporate_climber",
            "stable_provider",
            "women_forward",
            "globe_trotter",
            "mission_believer",
            "deep_specialist",
            "remote_first",
        }
        assert names == expected

    def test_synthetic_features_for_small_startup(self) -> None:
        features = {
            "headcount_estimate": "small",
            "funding_stage": "series_a",
            "wlb_score": 3.2,
            "remote_policy": "remote_first",
        }
        synth = derive_synthetic_features(features)
        assert synth["headcount_small_or_mid"] == 1.0
        assert synth["headcount_large_or_enterprise"] == 0.0
        assert synth["funding_early_stage"] == 1.0
        assert synth["remote_first_explicit"] == 1.0

    def test_founder_track_scores_high_on_startup(self) -> None:
        features = {
            "headcount_estimate": "small",
            "funding_stage": "series_a",
            "wlb_score": 3.5,
            "remote_policy": "flexible",
        }
        synth = derive_synthetic_features(features)
        score = score_company_against_archetype(synth, ARCHETYPES["founder_track"])
        # A small Series A company should score reasonably for founder_track
        assert score > 0.5

    def test_stable_provider_scores_high_on_enterprise_with_benefits(self) -> None:
        features = {
            "headcount_estimate": "enterprise",
            "funding_stage": "public",
            "wlb_score": 4.4,
            "parental_leave_weeks": 18,
            "remote_policy": "flexible",
        }
        synth = derive_synthetic_features(features)
        score = score_company_against_archetype(synth, ARCHETYPES["stable_provider"])
        assert score > 0.7

    def test_women_forward_requires_actual_signal(self) -> None:
        # Empty features should produce a low score, not a default-high one
        synth = derive_synthetic_features({})
        score = score_company_against_archetype(synth, ARCHETYPES["women_forward"])
        assert score < 0.5

    def test_remote_first_distinguishes_explicit_from_flexible(self) -> None:
        synth_explicit = derive_synthetic_features({"remote_policy": "remote_first"})
        synth_flexible = derive_synthetic_features({"remote_policy": "flexible"})
        explicit_score = score_company_against_archetype(synth_explicit, ARCHETYPES["remote_first"])
        flexible_score = score_company_against_archetype(synth_flexible, ARCHETYPES["remote_first"])
        assert explicit_score > flexible_score
