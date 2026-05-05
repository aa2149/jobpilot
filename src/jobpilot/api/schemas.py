# ============================================================================
# Copyright (c) 2026 Areej Ahmed. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Pydantic models for request/response shapes across the API."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


# ============================================================================
# Work mode + platform routing
# ============================================================================

WorkMode = Literal["onsite", "hybrid", "remote", "freelance"]


class PlatformInfo(BaseModel):
    id: str
    display_name: str
    domain: str
    kind: str
    work_modes: list[WorkMode]
    regions: list[str]
    status: Literal["live", "planned", "stub"]
    notes: str = ""


class PlatformsRequest(BaseModel):
    work_modes: list[WorkMode] = Field(default_factory=lambda: ["onsite", "hybrid", "remote"])
    regions: list[str] = Field(default_factory=lambda: ["global"])


class PlatformsResponse(BaseModel):
    platforms: list[PlatformInfo]
    total: int


# ============================================================================
# Apply endpoint
# ============================================================================

class Applicant(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    resume_path: str = Field(default="", description="Absolute path to a local PDF resume.")
    resume_text: str = Field(default="", description="Full text/markdown of the resume, used by the LLM.")
    work_auth: str | None = None
    preferred_pronouns: str | None = None


class ApplyOptions(BaseModel):
    auto_submit: bool = True
    headless: bool = True
    llm_model: str | None = None  # defaults to gemini-2.0-flash
    min_match_score: float = Field(0.0, ge=0.0, le=1.0)
    screenshot_on_failure: bool = True


class ApplyRequest(BaseModel):
    job_url: HttpUrl
    applicant: Applicant
    options: ApplyOptions = ApplyOptions()


ApplyState = Literal[
    "pre_submit_ready",
    "submitted",
    "below_fit_threshold",
    "invalid_payload",
    "job_not_found",
    "platform_unrecognized",
    "platform_not_implemented",
    "form_schema_unrecognized",
    "blocked_by_bot_detection",
    "llm_error",
    "upload_failed",
    "timeout",
    "unknown_error",
]


class ApplyResponse(BaseModel):
    status: Literal["success", "failure"]
    run_id: str
    state: ApplyState
    job_url: str
    fields_filled: int = 0
    questions_answered: int = 0
    resume_uploaded: bool = False
    duration_ms: int = 0
    screenshot: str | None = None
    logs_path: str | None = None
    reason: str | None = None
    step: str | None = None
    next_action: str | None = None


# ============================================================================
# Batch endpoint — apply to multiple jobs in sequence
# ============================================================================

class BatchRequest(BaseModel):
    job_urls: list[HttpUrl]
    applicant: Applicant
    options: ApplyOptions = Field(default_factory=ApplyOptions)
    pause_seconds: float = Field(8.0, ge=2.0, le=60.0)


class BatchJobResultModel(BaseModel):
    job_url: str
    run_id: str
    state: ApplyState
    company: str = ""
    role: str = ""
    fields_filled: int = 0
    questions_answered: int = 0
    resume_uploaded: bool = False
    duration_ms: int = 0
    screenshot: str | None = None
    reason: str | None = None


class BatchResponse(BaseModel):
    batch_id: str
    started_at: str
    finished_at: str
    total_jobs: int
    successes: int
    failures: int
    blocked: int
    results: list[BatchJobResultModel]
    tracker_path: str
    tracker_download_url: str
    email_eml_path: str = ""
    email_status: str = "stubbed"  # "stubbed" or "sent"


# ============================================================================
# Score endpoint (Fit Intelligence)
# ============================================================================

ArchetypeName = Literal[
    "founder_track",
    "corporate_climber",
    "stable_provider",
    "women_forward",
    "globe_trotter",
    "mission_believer",
    "deep_specialist",
    "remote_first",
]


class CandidateArchetype(BaseModel):
    name: ArchetypeName
    weight: float = Field(..., ge=0.0, le=1.0)


class ScoreRequest(BaseModel):
    job_url: HttpUrl
    candidate_archetypes: list[CandidateArchetype]


class Evidence(BaseModel):
    source: str
    claim: str
    url: str | None = None


class ScoreResponse(BaseModel):
    status: Literal["scored", "failed"]
    company: str | None = None
    fit_score: float = Field(..., ge=0.0, le=1.0)
    verdict: Literal["apply", "skip", "uncertain"]
    company_archetype_scores: dict[str, float] = {}
    reasoning: str = ""
    evidence: list[Evidence] = []
    cache_age_days: int | None = None
    error: str | None = None
