# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Glassdoor company-page scraper.

For v1 we keep this best-effort. Glassdoor blocks aggressively, and the
fit scorer is designed to degrade gracefully when this returns nothing.

Strategy:
  1. Search Glassdoor for the company name to find its overview URL
  2. Scrape ratings + a sample of reviews
  3. Cache 30 days

If at any point we hit a challenge page, we return empty data and the
scorer continues with whatever else it has.
"""
from __future__ import annotations

import urllib.parse
from typing import Any

from jobpilot.browser.launcher import stealth_page
from jobpilot.fit import cache
from jobpilot.config import settings


GLASSDOOR_BASE = "https://www.glassdoor.com"


async def fetch_glassdoor(company_name: str) -> tuple[dict[str, Any], int | None]:
    """Returns (data_dict, cache_age_days). data_dict has shape:
    {
        "overall_rating": float | None,
        "wlb_score": float | None,
        "culture_score": float | None,
        "reviews_sample": str,  # concatenated review text, truncated
    }
    """
    cached = cache.get("glassdoor", company_name.lower(), ttl_days=settings.fit_cache_reviews_days)
    if cached:
        return cached[0], cached[1]

    data: dict[str, Any] = {
        "overall_rating": None,
        "wlb_score": None,
        "culture_score": None,
        "reviews_sample": "",
    }

    try:
        async with stealth_page() as page:
            search_url = f"{GLASSDOOR_BASE}/Search/results.htm?keyword={urllib.parse.quote(company_name)}"
            await page.goto(search_url, timeout=15_000, wait_until="domcontentloaded")

            # Did we hit a challenge?
            url = page.url.lower()
            if "challenge" in url or "cdn-cgi" in url:
                cache.put("glassdoor", data, company_name.lower())
                return data, 0

            # Best-effort: grab any star ratings visible on the page
            try:
                rating_loc = page.locator("[data-test='rating'], [class*='rating']").first
                if await rating_loc.count() > 0:
                    text = (await rating_loc.inner_text(timeout=1500)).strip()
                    try:
                        data["overall_rating"] = float(text.split()[0])
                    except (ValueError, IndexError):
                        pass
            except Exception:
                pass

            # Try to grab a chunk of review-page text. We don't drill into the
            # full review structure for v1 — the LLM extraction layer can
            # work with raw text.
            try:
                main_text = await page.locator("body").inner_text(timeout=2500)
                if main_text:
                    # Trim to a reasonable size
                    data["reviews_sample"] = main_text[:6000]
            except Exception:
                pass
    except Exception:
        # Any failure: return empty data so the scorer can proceed
        pass

    cache.put("glassdoor", data, company_name.lower())
    return data, 0
