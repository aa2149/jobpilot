# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Best-effort careers/about-page scraper.

We try a handful of common paths for company sites: /careers, /about,
/team, /culture. We grab visible text and let the LLM feature extractor
do the work.
"""
from __future__ import annotations

import urllib.parse
from typing import Any

from jobpilot.browser.launcher import stealth_page
from jobpilot.fit import cache
from jobpilot.config import settings


COMMON_PATHS = ["/careers", "/about", "/team", "/culture", "/jobs", "/values"]


async def fetch_careers_page(company_name: str, hint_url: str | None = None) -> tuple[dict[str, Any], int | None]:
    """Returns ({"text": str, "url": str | None}, cache_age_days)."""
    cached = cache.get("careers", company_name.lower(), ttl_days=settings.fit_cache_careers_days)
    if cached:
        return cached[0], cached[1]

    data: dict[str, Any] = {"text": "", "url": None}

    candidates: list[str] = []
    if hint_url:
        candidates.append(hint_url)

    # Best guess: company.com
    slug = company_name.lower().replace(" ", "")
    if slug:
        for path in COMMON_PATHS:
            candidates.append(f"https://{slug}.com{path}")

    try:
        async with stealth_page() as page:
            for url in candidates[:4]:  # cap how many we try
                try:
                    response = await page.goto(url, timeout=10_000, wait_until="domcontentloaded")
                    if response and response.ok:
                        text = await page.locator("body").inner_text(timeout=2000)
                        if text and len(text) > 500:
                            data = {"text": text[:8000], "url": url}
                            break
                except Exception:
                    continue
    except Exception:
        pass

    cache.put("careers", data, company_name.lower())
    return data, 0
