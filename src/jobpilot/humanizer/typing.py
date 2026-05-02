# ============================================================================
# Copyright (c) 2026 [YOUR NAME]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Human-like typing.

The aim is to never produce a constant-rate keystream. Anti-bot systems score
behavioral signals; the typing fingerprint of a script that types every
character at exactly 50ms is unmistakable.

Approach: per-character delay drawn from a log-normal distribution (mean ~120ms,
sigma ~40ms in linear space). Occasional longer pauses (think-pause) inserted
at word boundaries with low probability. Realistic typo-and-correct behavior is
NOT included in v1 — it is a future hardening step.
"""
from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from playwright.async_api import ElementHandle, Page


# Tunable constants. Chosen to mimic a moderate-speed (~50 WPM) typist.
MEAN_DELAY_MS = 120.0
SIGMA_DELAY_MS = 40.0
THINK_PAUSE_PROB = 0.04  # 4% of word boundaries get a longer pause
THINK_PAUSE_RANGE_MS = (500, 1800)


def _delay_ms() -> float:
    """Draw a single keystroke delay from log-normal (clipped to sane range)."""
    # Convert (mean, sigma) in linear space to log-normal parameters
    mu = np.log(MEAN_DELAY_MS**2 / np.sqrt(MEAN_DELAY_MS**2 + SIGMA_DELAY_MS**2))
    sigma = np.sqrt(np.log(1 + (SIGMA_DELAY_MS**2 / MEAN_DELAY_MS**2)))
    val = float(np.random.lognormal(mu, sigma))
    return max(35.0, min(val, 600.0))


async def human_type(page: "Page", selector: str, text: str) -> None:
    """Click into a field, then type one character at a time with humanized delays."""
    locator = page.locator(selector).first
    await locator.scroll_into_view_if_needed()
    await locator.click()
    await _type_into_focused(page, text)


async def human_type_locator(locator, text: str) -> None:
    """Variant for when caller already has a locator."""
    await locator.scroll_into_view_if_needed()
    await locator.click()
    page = locator.page  # type: ignore[attr-defined]
    await _type_into_focused(page, text)


async def _type_into_focused(page: "Page", text: str) -> None:
    last_was_space = False
    for ch in text:
        await page.keyboard.type(ch, delay=_delay_ms())
        if ch == " ":
            last_was_space = True
        else:
            # End of word: occasionally pause to "think"
            if last_was_space and random.random() < THINK_PAUSE_PROB:
                pause = random.randint(*THINK_PAUSE_RANGE_MS) / 1000.0
                await asyncio.sleep(pause)
            last_was_space = False
