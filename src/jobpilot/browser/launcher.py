# ============================================================================
# Copyright (c) 2026 [YOUR NAME]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Stealth browser launcher.

Two stealth profiles are supported:
  - patchright (default, preferred): drop-in Playwright replacement with CDP-level patches
  - playwright_stealth: Microsoft Playwright + JS-layer stealth patches (fallback)

Both expose the same Page API. The launcher returns an async context manager
that yields a page already configured with realistic viewport, locale, and UA.
"""
from __future__ import annotations

import random
from contextlib import asynccontextmanager
from typing import AsyncIterator

from jobpilot.config import settings


# Realistic desktop viewport distribution. Sampled at random per launch
# so we are not always 1920x1080.
VIEWPORT_POOL = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1680, "height": 1050},
    {"width": 1280, "height": 800},
]

# Locale + timezone pairs. The pair must be self-consistent.
LOCALE_TZ_POOL = [
    ("en-US", "America/New_York"),
    ("en-US", "America/Los_Angeles"),
    ("en-US", "America/Chicago"),
    ("en-GB", "Europe/London"),
    ("en-AE", "Asia/Dubai"),
    ("en-SG", "Asia/Singapore"),
]


@asynccontextmanager
async def stealth_page() -> AsyncIterator:
    """Launch a stealth browser, yield a page, clean up on exit."""
    viewport = random.choice(VIEWPORT_POOL)
    locale, tz = random.choice(LOCALE_TZ_POOL)

    proxy_arg = None
    if settings.proxy_url:
        proxy_arg = {"server": settings.proxy_url}

    if settings.stealth_profile == "patchright":
        # Patchright is a drop-in Playwright replacement with stronger stealth.
        from patchright.async_api import async_playwright  # type: ignore[import-not-found]

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=settings.headless,
                proxy=proxy_arg,
            )
            context = await browser.new_context(
                viewport=viewport,
                locale=locale,
                timezone_id=tz,
                ignore_https_errors=False,
            )
            if settings.har_capture:
                # HAR is captured per-context.
                pass  # placeholder; record_har_path needs a path before context creation

            page = await context.new_page()
            try:
                yield page
            finally:
                await context.close()
                await browser.close()
    else:
        # Fallback: vanilla Playwright + playwright-stealth patches
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=settings.headless,
                proxy=proxy_arg,
            )
            context = await browser.new_context(
                viewport=viewport,
                locale=locale,
                timezone_id=tz,
            )
            page = await context.new_page()
            await Stealth().apply_stealth_async(page)
            try:
                yield page
            finally:
                await context.close()
                await browser.close()
