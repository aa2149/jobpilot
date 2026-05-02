# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Artifact capture helpers — screenshots and DOM snapshots per run."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from jobpilot.observability.logger import run_dir

if TYPE_CHECKING:
    from playwright.async_api import Page


async def capture_screenshot(page: "Page", run_id: str, name: str = "pre_submit") -> Path:
    """Full-page screenshot to logs/<run_id>/<name>.png."""
    path = run_dir(run_id) / f"{name}.png"
    await page.screenshot(path=str(path), full_page=True)
    return path


async def capture_dom_snapshot(page: "Page", run_id: str, name: str = "dom_snapshot") -> Path:
    """Save full HTML to logs/<run_id>/<name>.html."""
    html = await page.content()
    path = run_dir(run_id) / f"{name}.html"
    path.write_text(html, encoding="utf-8")
    return path
