# ============================================================================
# Copyright (c) 2026 Areej Ahmed. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""The platform graph.

Maps work modes (onsite/hybrid/remote/freelance) and regions (UAE-specific,
global, etc.) to the right set of job platforms. The router uses this to
decide which adapters to engage for a given candidate's preferences.

This is the spine of multi-platform support. Adding a new platform means:
  1. Add an entry here
  2. Implement the adapter under flow/adapters/
  3. Register it in the adapter registry

Adapters NOT YET IMPLEMENTED in v1 are marked with status="planned".
v1 ships full Greenhouse support, with everything else mapped but stub-only,
so a developer (or our future selves) can fill them in incrementally.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


WorkMode = Literal["onsite", "hybrid", "remote", "freelance"]
PlatformKind = Literal["aggregator", "ats", "remote_first", "freelance", "regional", "recruiter"]
Status = Literal["live", "planned", "stub"]


@dataclass(frozen=True)
class Platform:
    id: str
    display_name: str
    domain: str
    kind: PlatformKind
    work_modes: tuple[WorkMode, ...]
    regions: tuple[str, ...]  # ISO country codes or "global"
    status: Status
    notes: str = ""


# =============================================================================
# THE PLATFORM GRAPH
# =============================================================================

PLATFORMS: dict[str, Platform] = {
    # ---------- Major aggregators (global) ----------
    "linkedin": Platform(
        id="linkedin",
        display_name="LinkedIn",
        domain="linkedin.com/jobs",
        kind="aggregator",
        work_modes=("onsite", "hybrid", "remote"),
        regions=("global",),
        status="planned",
        notes="Easy Apply varies wildly. Strong for onsite/hybrid roles. Bot-detection is heavy.",
    ),
    "indeed": Platform(
        id="indeed",
        display_name="Indeed",
        domain="indeed.com",
        kind="aggregator",
        work_modes=("onsite", "hybrid", "remote"),
        regions=("global",),
        status="planned",
        notes="High volume, low signal. Most listings are aggregated from elsewhere.",
    ),
    "glassdoor": Platform(
        id="glassdoor",
        display_name="Glassdoor",
        domain="glassdoor.com",
        kind="aggregator",
        work_modes=("onsite", "hybrid", "remote"),
        regions=("global",),
        status="stub",
        notes="We use Glassdoor primarily as a fit-intelligence source, not an application target.",
    ),

    # ---------- ATS (where companies host their own postings) ----------
    "greenhouse": Platform(
        id="greenhouse",
        display_name="Greenhouse",
        domain="greenhouse.io",
        kind="ats",
        work_modes=("onsite", "hybrid", "remote"),
        regions=("global",),
        status="live",
        notes="THE flagship adapter. Full v1 support.",
    ),
    "lever": Platform(
        id="lever",
        display_name="Lever",
        domain="lever.co",
        kind="ats",
        work_modes=("onsite", "hybrid", "remote"),
        regions=("global",),
        status="planned",
    ),
    "ashby": Platform(
        id="ashby",
        display_name="Ashby",
        domain="ashbyhq.com",
        kind="ats",
        work_modes=("onsite", "hybrid", "remote"),
        regions=("global",),
        status="planned",
    ),
    "workday": Platform(
        id="workday",
        display_name="Workday",
        domain="myworkdayjobs.com",
        kind="ats",
        work_modes=("onsite", "hybrid", "remote"),
        regions=("global",),
        status="planned",
        notes="Notoriously inconsistent. Each company customizes the form.",
    ),

    # ---------- UAE / Gulf regional ----------
    "naukrigulf": Platform(
        id="naukrigulf",
        display_name="Naukrigulf",
        domain="naukrigulf.com",
        kind="regional",
        work_modes=("onsite", "hybrid"),
        regions=("AE", "SA", "QA", "KW", "BH", "OM"),
        status="planned",
        notes="The dominant Gulf job board. Onsite-heavy.",
    ),
    "gulftalent": Platform(
        id="gulftalent",
        display_name="GulfTalent",
        domain="gulftalent.com",
        kind="regional",
        work_modes=("onsite", "hybrid"),
        regions=("AE", "SA", "QA", "KW", "BH", "OM"),
        status="planned",
    ),
    "bayt": Platform(
        id="bayt",
        display_name="Bayt.com",
        domain="bayt.com",
        kind="regional",
        work_modes=("onsite", "hybrid"),
        regions=("AE", "SA", "EG", "JO", "LB"),
        status="planned",
    ),

    # ---------- Remote-first ----------
    "weworkremotely": Platform(
        id="weworkremotely",
        display_name="We Work Remotely",
        domain="weworkremotely.com",
        kind="remote_first",
        work_modes=("remote",),
        regions=("global",),
        status="planned",
    ),
    "remoteok": Platform(
        id="remoteok",
        display_name="Remote OK",
        domain="remoteok.com",
        kind="remote_first",
        work_modes=("remote",),
        regions=("global",),
        status="planned",
        notes="Has a clean public JSON feed. Easiest to integrate.",
    ),
    "remotive": Platform(
        id="remotive",
        display_name="Remotive",
        domain="remotive.com",
        kind="remote_first",
        work_modes=("remote",),
        regions=("global",),
        status="planned",
    ),
    "flexjobs": Platform(
        id="flexjobs",
        display_name="FlexJobs",
        domain="flexjobs.com",
        kind="remote_first",
        work_modes=("remote", "freelance"),
        regions=("global",),
        status="planned",
        notes="Paid platform. Adapter would need credentials.",
    ),
    "jobspresso": Platform(
        id="jobspresso",
        display_name="Jobspresso",
        domain="jobspresso.co",
        kind="remote_first",
        work_modes=("remote",),
        regions=("global",),
        status="planned",
    ),
    "workingnomads": Platform(
        id="workingnomads",
        display_name="Working Nomads",
        domain="workingnomads.com",
        kind="remote_first",
        work_modes=("remote",),
        regions=("global",),
        status="planned",
    ),
    "justremote": Platform(
        id="justremote",
        display_name="JustRemote",
        domain="justremote.co",
        kind="remote_first",
        work_modes=("remote",),
        regions=("global",),
        status="planned",
    ),
    "jobgether": Platform(
        id="jobgether",
        display_name="Jobgether",
        domain="jobgether.com",
        kind="remote_first",
        work_modes=("remote", "hybrid"),
        regions=("global",),
        status="planned",
    ),
    "remoteco": Platform(
        id="remoteco",
        display_name="Remote.co",
        domain="remote.co",
        kind="remote_first",
        work_modes=("remote",),
        regions=("global",),
        status="planned",
    ),
    "wellfound": Platform(
        id="wellfound",
        display_name="Wellfound (formerly AngelList)",
        domain="wellfound.com",
        kind="remote_first",
        work_modes=("remote", "hybrid", "onsite"),
        regions=("global",),
        status="planned",
        notes="Best for startup roles. Equity transparency.",
    ),
    "web3jobs": Platform(
        id="web3jobs",
        display_name="Web3 Jobs",
        domain="web3.career",
        kind="remote_first",
        work_modes=("remote",),
        regions=("global",),
        status="planned",
    ),
    "efinancialcareers": Platform(
        id="efinancialcareers",
        display_name="eFinancialCareers",
        domain="efinancialcareers.com",
        kind="aggregator",
        work_modes=("onsite", "hybrid", "remote"),
        regions=("global",),
        status="planned",
        notes="Finance / banking specialist board.",
    ),

    # ---------- Freelance / contract ----------
    "upwork": Platform(
        id="upwork",
        display_name="Upwork",
        domain="upwork.com",
        kind="freelance",
        work_modes=("freelance",),
        regions=("global",),
        status="planned",
        notes="Proposal-based, not application-based. Adapter logic differs significantly.",
    ),
    "fiverr": Platform(
        id="fiverr",
        display_name="Fiverr",
        domain="fiverr.com",
        kind="freelance",
        work_modes=("freelance",),
        regions=("global",),
        status="planned",
        notes="Gig-based, supplier-side. The 'application' is creating a gig listing.",
    ),
    "toptal": Platform(
        id="toptal",
        display_name="Toptal",
        domain="toptal.com",
        kind="freelance",
        work_modes=("freelance",),
        regions=("global",),
        status="planned",
        notes="Vetted freelance network. Application is invitation-based.",
    ),

    # ---------- UAE recruitment agencies ----------
    "hays": Platform(
        id="hays",
        display_name="Hays",
        domain="hays.ae",
        kind="recruiter",
        work_modes=("onsite", "hybrid"),
        regions=("AE", "global"),
        status="planned",
    ),
    "michaelpage": Platform(
        id="michaelpage",
        display_name="Michael Page",
        domain="michaelpage.ae",
        kind="recruiter",
        work_modes=("onsite", "hybrid"),
        regions=("AE", "global"),
        status="planned",
    ),
    "manpower": Platform(
        id="manpower",
        display_name="Manpower",
        domain="manpower.ae",
        kind="recruiter",
        work_modes=("onsite", "hybrid"),
        regions=("AE", "global"),
        status="planned",
    ),
    "cooperfitch": Platform(
        id="cooperfitch",
        display_name="Cooper Fitch",
        domain="cooperfitch.ae",
        kind="recruiter",
        work_modes=("onsite", "hybrid"),
        regions=("AE",),
        status="planned",
    ),
    "charterhouse": Platform(
        id="charterhouse",
        display_name="Charterhouse",
        domain="charterhouseme.ae",
        kind="recruiter",
        work_modes=("onsite", "hybrid"),
        regions=("AE",),
        status="planned",
    ),
    "marcellis": Platform(
        id="marcellis",
        display_name="Marc Ellis",
        domain="marcellis.com",
        kind="recruiter",
        work_modes=("onsite", "hybrid"),
        regions=("AE",),
        status="planned",
    ),
    "salt": Platform(
        id="salt",
        display_name="Salt",
        domain="welovesalt.com",
        kind="recruiter",
        work_modes=("onsite", "hybrid", "remote"),
        regions=("AE", "global"),
        status="planned",
    ),
    "mcgtalent": Platform(
        id="mcgtalent",
        display_name="MCG Talent",
        domain="mcgtalent.com",
        kind="recruiter",
        work_modes=("onsite", "hybrid"),
        regions=("AE",),
        status="planned",
    ),
    "adecco": Platform(
        id="adecco",
        display_name="Adecco",
        domain="adecco.ae",
        kind="recruiter",
        work_modes=("onsite", "hybrid"),
        regions=("AE", "global"),
        status="planned",
    ),
}


# =============================================================================
# ROUTING
# =============================================================================

def platforms_for(work_modes: list[WorkMode], regions: list[str] | None = None) -> list[Platform]:
    """Return platforms whose work_modes intersect the request and whose
    regions include any of the requested regions (or 'global').
    """
    regions_set = set(regions or ["global"])
    matches: list[Platform] = []
    for p in PLATFORMS.values():
        # Work mode must overlap
        if not set(work_modes).intersection(p.work_modes):
            continue
        # Region must overlap (or platform is global)
        plat_regions = set(p.regions)
        if "global" in plat_regions or plat_regions.intersection(regions_set):
            matches.append(p)
    # Sort: live > stub > planned, then by display_name
    status_order = {"live": 0, "stub": 1, "planned": 2}
    matches.sort(key=lambda p: (status_order[p.status], p.display_name))
    return matches


def detect_platform(url: str) -> Platform | None:
    """Best-effort identification of a platform from a URL."""
    lower = url.lower()
    for plat in PLATFORMS.values():
        if plat.domain.lower() in lower:
            return plat
    return None


def adapter_status(platform_id: str) -> Status:
    p = PLATFORMS.get(platform_id)
    return p.status if p else "planned"
