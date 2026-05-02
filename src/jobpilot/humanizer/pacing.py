# ============================================================================
# Copyright (c) 2026 [YOUR NAME]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Pacing helpers: idle pauses between sections, realistic scrolling."""
from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page


async def section_pause() -> None:
    """1-4 second pause between major form sections."""
    await asyncio.sleep(random.uniform(1.0, 4.0))


async def micro_pause() -> None:
    """200-700ms pause, e.g. before clicking submit-adjacent buttons."""
    await asyncio.sleep(random.uniform(0.2, 0.7))


async def human_scroll(page: "Page", *, distance: int | None = None) -> None:
    """Scroll the page by a randomized amount, in 2-4 small ticks."""
    target = distance if distance is not None else random.randint(200, 600)
    ticks = random.randint(2, 4)
    per_tick = target // ticks
    for _ in range(ticks):
        await page.mouse.wheel(0, per_tick + random.randint(-30, 30))
        await asyncio.sleep(random.uniform(0.08, 0.22))


async def occasional_scroll_back(page: "Page") -> None:
    """Sometimes humans scroll up to re-read. ~15% of section transitions."""
    if random.random() < 0.15:
        await page.mouse.wheel(0, -random.randint(150, 350))
        await asyncio.sleep(random.uniform(0.4, 1.1))
