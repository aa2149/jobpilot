# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""The application router.

POST /apply hits this. We:
  1. Detect the platform from the URL
  2. Look up the right adapter
  3. Run it
  4. Return the structured result

If we cannot detect the platform, we return platform_unrecognized so
the user gets a useful error instead of an opaque failure.
"""
from __future__ import annotations

from jobpilot.api.schemas import Applicant, ApplyOptions
from jobpilot.flow.adapters.base import AdapterContext, get_adapter
from jobpilot.flow.greenhouse import FlowResult
from jobpilot.platforms.graph import detect_platform


async def route_and_apply(
    *,
    run_id: str,
    job_url: str,
    applicant: Applicant,
    options: ApplyOptions,
) -> FlowResult:
    platform = detect_platform(job_url)

    if platform is None:
        return FlowResult(
            state="job_not_found",
            reason=(
                "Unrecognized platform. v1 supports Greenhouse-hosted jobs "
                "(greenhouse.io subdomains, plus career pages with ?gh_jid=...). "
                "Multi-platform routing for LinkedIn, Indeed, Lever, Workday, "
                "Naukrigulf, Upwork, etc. is on the roadmap."
            ),
            step="route",
        )

    adapter = get_adapter(platform.id, platform.display_name)
    ctx = AdapterContext(
        run_id=run_id,
        job_url=job_url,
        applicant=applicant,
        options=options,
    )
    return await adapter.run(ctx)
