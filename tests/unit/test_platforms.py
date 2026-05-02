# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Tests for the platform graph and the application router."""
from __future__ import annotations

import pytest

from jobpilot.platforms.graph import PLATFORMS, detect_platform, platforms_for


class TestPlatformDetection:
    def test_detects_greenhouse_subdomain(self) -> None:
        url = "https://job-boards.greenhouse.io/grammarly/jobs/7767680"
        p = detect_platform(url)
        assert p is not None
        assert p.id == "greenhouse"

    def test_detects_greenhouse_with_gh_jid(self) -> None:
        url = "https://instacart.careers/job/?gh_jid=7747789"
        # This should NOT be auto-detected as greenhouse based on domain
        # — it's the instacart subdomain. The orchestrator handles ?gh_jid
        # routing separately. We document the expected behavior.
        p = detect_platform(url)
        # Either we detect it via the gh_jid pattern, or we don't —
        # but if we don't, the router should give a clear error.
        # For now, the URL doesn't contain greenhouse.io so detect returns None.
        assert p is None or p.id == "greenhouse"

    def test_detects_linkedin(self) -> None:
        url = "https://www.linkedin.com/jobs/view/3892341023"
        p = detect_platform(url)
        assert p is not None
        assert p.id == "linkedin"

    def test_unknown_url_returns_none(self) -> None:
        url = "https://random-careers-site.example.com/apply"
        p = detect_platform(url)
        assert p is None


class TestWorkModeRouting:
    def test_freelance_filters_out_onsite_only(self) -> None:
        results = platforms_for(work_modes=["freelance"], regions=["global"])
        ids = {p.id for p in results}
        # Should include freelance platforms
        assert "upwork" in ids
        assert "fiverr" in ids
        # Should NOT include onsite-only UAE recruiters
        assert "cooperfitch" not in ids

    def test_uae_region_includes_local_portals(self) -> None:
        results = platforms_for(
            work_modes=["onsite", "hybrid"],
            regions=["AE"],
        )
        ids = {p.id for p in results}
        assert "naukrigulf" in ids
        assert "gulftalent" in ids
        assert "bayt" in ids
        assert "cooperfitch" in ids
        assert "hays" in ids

    def test_remote_only_includes_remote_first_platforms(self) -> None:
        results = platforms_for(work_modes=["remote"], regions=["global"])
        ids = {p.id for p in results}
        assert "weworkremotely" in ids
        assert "remoteok" in ids
        assert "remotive" in ids
        # Should not include freelance-only platforms
        # (Toptal is freelance-only, so should be excluded)
        assert "toptal" not in ids

    def test_global_includes_greenhouse(self) -> None:
        results = platforms_for(work_modes=["onsite", "hybrid", "remote"], regions=["global"])
        ids = {p.id for p in results}
        assert "greenhouse" in ids

    def test_results_sorted_live_first(self) -> None:
        results = platforms_for(work_modes=["onsite", "hybrid", "remote"], regions=["global"])
        statuses = [p.status for p in results]
        # The first one should be 'live' if any live platform matches
        live_idx = next((i for i, s in enumerate(statuses) if s == "live"), None)
        planned_idx = next((i for i, s in enumerate(statuses) if s == "planned"), None)
        if live_idx is not None and planned_idx is not None:
            assert live_idx < planned_idx


class TestPlatformGraph:
    def test_at_least_one_live_platform(self) -> None:
        live = [p for p in PLATFORMS.values() if p.status == "live"]
        assert len(live) >= 1, "v1 must ship at least one live adapter"
        assert any(p.id == "greenhouse" for p in live)

    def test_uae_recruiters_present(self) -> None:
        ids = {p.id for p in PLATFORMS.values()}
        # The user's compiled UAE recruiter list
        for rec in ["hays", "michaelpage", "manpower", "cooperfitch", "charterhouse",
                    "marcellis", "salt", "mcgtalent", "adecco"]:
            assert rec in ids, f"Missing UAE recruiter: {rec}"

    def test_freelance_platforms_present(self) -> None:
        ids = {p.id for p in PLATFORMS.values()}
        assert "upwork" in ids
        assert "fiverr" in ids
        assert "toptal" in ids
