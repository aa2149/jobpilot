# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Bezier-curve mouse movement.

Anti-bot systems flag straight-line cursor movements between elements. Real
humans produce curved paths with varying speed. We approximate this with a
quadratic Bezier between source and target, with a randomized control point.
"""
from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page


def _bezier_point(t: float, p0: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float]) -> tuple[float, float]:
    one_minus_t = 1.0 - t
    x = one_minus_t**2 * p0[0] + 2 * one_minus_t * t * p1[0] + t**2 * p2[0]
    y = one_minus_t**2 * p0[1] + 2 * one_minus_t * t * p1[1] + t**2 * p2[1]
    return x, y


async def human_move_to(page: "Page", target_x: float, target_y: float, *, steps: int = 25) -> None:
    """Move the mouse to (target_x, target_y) along a curved path."""
    # Start from a sensible default if we don't know the current position.
    # Playwright doesn't expose mouse position, so we approximate.
    start_x = random.uniform(target_x - 200, target_x + 200)
    start_y = random.uniform(target_y - 150, target_y + 150)
    # Random control point creates the curve
    ctrl_x = (start_x + target_x) / 2 + random.uniform(-100, 100)
    ctrl_y = (start_y + target_y) / 2 + random.uniform(-100, 100)

    p0 = (start_x, start_y)
    p1 = (ctrl_x, ctrl_y)
    p2 = (target_x, target_y)

    for i in range(1, steps + 1):
        t = i / steps
        x, y = _bezier_point(t, p0, p1, p2)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.005, 0.020))
