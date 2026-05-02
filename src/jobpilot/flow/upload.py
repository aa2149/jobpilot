# ============================================================================
# Copyright (c) 2026 [YOUR NAME]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Resume / file upload to a Greenhouse form."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page


async def upload_resume(page: "Page", file_input_selector: str, resume_path: str) -> None:
    """Upload the resume PDF and wait for the upload to settle."""
    path = Path(resume_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {path}")
    if path.suffix.lower() not in {".pdf", ".doc", ".docx", ".txt"}:
        raise ValueError(f"Unsupported resume format: {path.suffix}")

    loc = page.locator(file_input_selector).first
    await loc.set_input_files(str(path))

    # Greenhouse shows an upload progress / filename indicator. Give it a beat
    # to settle. We don't fail if the indicator never appears.
    try:
        await page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass

    # Quick stabilization pause
    await asyncio.sleep(1.0)
