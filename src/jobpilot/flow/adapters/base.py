# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Adapter base + registry.

An adapter knows how to drive an application on one specific platform.
The router takes a job URL → detects the platform → looks up the adapter →
runs it. v1 ships only the Greenhouse adapter as fully implemented;
everything else is a stub so the user sees a clear "not yet implemented"
message instead of a crash.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jobpilot.api.schemas import Applicant, ApplyOptions
    from jobpilot.flow.greenhouse import FlowResult


@dataclass
class AdapterContext:
    run_id: str
    job_url: str
    applicant: "Applicant"
    options: "ApplyOptions"


class Adapter(ABC):
    """Implement one of these per platform."""

    platform_id: str  # must match Platform.id in graph.py

    @abstractmethod
    async def run(self, ctx: AdapterContext) -> "FlowResult":
        ...


# ---------------------------------------------------------------------------
# Concrete adapters
# ---------------------------------------------------------------------------

class GreenhouseAdapter(Adapter):
    platform_id = "greenhouse"

    async def run(self, ctx: AdapterContext) -> "FlowResult":
        from jobpilot.flow.greenhouse import run_apply
        return await run_apply(
            run_id=ctx.run_id,
            job_url=ctx.job_url,
            applicant=ctx.applicant,
            options=ctx.options,
        )


class StubAdapter(Adapter):
    """Used for any platform that isn't implemented yet. Returns a
    structured 'not yet implemented' result so the API caller knows
    exactly why nothing happened.
    """
    def __init__(self, platform_id: str, display_name: str):
        self.platform_id = platform_id
        self._display_name = display_name

    async def run(self, ctx: AdapterContext) -> "FlowResult":
        from jobpilot.flow.greenhouse import FlowResult
        return FlowResult(
            state="form_schema_unrecognized",
            reason=f"{self._display_name} adapter not yet implemented in v1. "
                   f"v1 ships full Greenhouse support; this platform is on the roadmap.",
            step="route",
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, Adapter] = {
    "greenhouse": GreenhouseAdapter(),
}


def get_adapter(platform_id: str, display_name: str = "") -> Adapter:
    """Lookup, with stub fallback for unimplemented platforms."""
    if platform_id in _REGISTRY:
        return _REGISTRY[platform_id]
    return StubAdapter(platform_id, display_name or platform_id)
