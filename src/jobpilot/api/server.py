# ============================================================================
# Copyright (c) 2026 [YOUR NAME]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""FastAPI server. Exposes:

  POST /apply       — drive an application via the right platform adapter
  POST /score       — score a job against the candidate's archetypes
  POST /platforms   — discover platforms for a given work-mode + region set
  GET  /archetypes  — list the eight archetypes (frontend onboarding)
  GET  /health      — basic liveness
"""
from __future__ import annotations

import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from jobpilot.api.schemas import (
    ApplyRequest,
    ApplyResponse,
    BatchJobResultModel,
    BatchRequest,
    BatchResponse,
    PlatformInfo,
    PlatformsRequest,
    PlatformsResponse,
    ScoreRequest,
    ScoreResponse,
)
from jobpilot.config import settings
from jobpilot.fit.archetypes import ARCHETYPES
from jobpilot.fit.scorer import score_job
from jobpilot.flow.batch import run_batch
from jobpilot.flow.router import route_and_apply
from jobpilot.observability.logger import configure, get_run_logger, log_path, make_run_id, run_dir
from jobpilot.platforms.graph import PLATFORMS, platforms_for


app = FastAPI(
    title="JobPilot — Stealth Agent + Fit Intelligence",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    configure()


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "version": "0.3.0",
        "llm_provider": "gemini",
        "llm_model": settings.llm_model,
        "stealth_profile": settings.stealth_profile,
        "auto_submit_default": settings.auto_submit,
        "platforms_supported": sum(1 for p in PLATFORMS.values() if p.status == "live"),
        "platforms_total": len(PLATFORMS),
    }


@app.get("/archetypes")
async def list_archetypes() -> dict:
    return {
        "archetypes": [
            {"name": a.name, "display_name": a.display_name, "description": a.description}
            for a in ARCHETYPES.values()
        ]
    }


@app.post("/platforms", response_model=PlatformsResponse)
async def list_platforms(req: PlatformsRequest) -> PlatformsResponse:
    """Return the platforms relevant to a work-mode + region preference set."""
    matches = platforms_for(work_modes=req.work_modes, regions=req.regions)
    return PlatformsResponse(
        platforms=[
            PlatformInfo(
                id=p.id,
                display_name=p.display_name,
                domain=p.domain,
                kind=p.kind,
                work_modes=list(p.work_modes),
                regions=list(p.regions),
                status=p.status,
                notes=p.notes,
            )
            for p in matches
        ],
        total=len(matches),
    )


@app.post("/apply", response_model=ApplyResponse)
async def apply(req: ApplyRequest) -> ApplyResponse:
    run_id = make_run_id()
    log = get_run_logger(run_id)
    log.info("apply.received", job_url=str(req.job_url))

    started = time.monotonic()
    try:
        result = await route_and_apply(
            run_id=run_id,
            job_url=str(req.job_url),
            applicant=req.applicant,
            options=req.options,
        )
    except Exception as e:
        log.exception("apply.unhandled", error=str(e))
        raise HTTPException(status_code=500, detail=f"unhandled: {e}")

    duration = int((time.monotonic() - started) * 1000)
    is_success = result.state in ("pre_submit_ready", "submitted", "below_fit_threshold")

    return ApplyResponse(
        status="success" if is_success else "failure",
        run_id=run_id,
        state=result.state,
        job_url=str(req.job_url),
        fields_filled=result.fields_filled,
        questions_answered=result.questions_answered,
        resume_uploaded=result.resume_uploaded,
        duration_ms=duration,
        screenshot=result.screenshot,
        logs_path=str(log_path(run_id)),
        reason=result.reason,
        step=result.step,
        next_action="review_and_submit_manually" if result.state == "pre_submit_ready" else None,
    )


@app.post("/score", response_model=ScoreResponse)
async def score(req: ScoreRequest) -> ScoreResponse:
    return await score_job(str(req.job_url), req.candidate_archetypes)


@app.post("/batch", response_model=BatchResponse)
async def batch(req: BatchRequest) -> BatchResponse:
    """Apply to multiple jobs in sequence. Returns per-job results and a
    path to a personalized tracker xlsx that the user can download.
    """
    result = await run_batch(
        job_urls=[str(u) for u in req.job_urls],
        applicant=req.applicant,
        options=req.options,
        pause_seconds=req.pause_seconds,
    )
    return BatchResponse(
        batch_id=result.batch_id,
        started_at=result.started_at,
        finished_at=result.finished_at,
        total_jobs=result.total_jobs,
        successes=result.successes,
        failures=result.failures,
        blocked=result.blocked,
        tracker_path=result.tracker_path,
        tracker_download_url=f"/tracker/{result.batch_id}",
        email_eml_path=result.email_eml_path,
        email_status="sent" if settings.email_enabled else "stubbed",
        results=[
            BatchJobResultModel(
                job_url=r.job_url,
                run_id=r.run_id,
                state=r.state,
                company=r.company,
                role=r.role,
                fields_filled=r.fields_filled,
                questions_answered=r.questions_answered,
                resume_uploaded=r.resume_uploaded,
                duration_ms=r.duration_ms,
                screenshot=r.screenshot,
                reason=r.reason,
            )
            for r in result.results
        ],
    )


@app.get("/tracker/{batch_id}")
async def download_tracker(batch_id: str):
    """Download the per-batch tracker xlsx. Validates the batch_id format
    to prevent path traversal."""
    import re
    if not re.match(r"^batch_[\w\-:]+$", batch_id):
        raise HTTPException(status_code=400, detail="invalid batch_id format")

    path = run_dir(batch_id) / "tracker.xlsx"
    if not path.exists():
        raise HTTPException(status_code=404, detail="tracker not found for that batch")

    return FileResponse(
        path=str(path),
        filename=f"jobpilot_tracker_{batch_id}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
