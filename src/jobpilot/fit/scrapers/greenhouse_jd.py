# ============================================================================
# Copyright (c) 2026 Areej Ahmed. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Extract JD text and company name from a Greenhouse job page.

This scraper shares the stealth browser stack with the application agent.
For fit scoring, we just need the visible JD content and a guess at the
company name (Greenhouse subdomain or the job-board path segment).
"""
from __future__ import annotations

from urllib.parse import urlparse

from jobpilot.browser.launcher import stealth_page


async def scrape_jd(job_url: str) -> tuple[str, str]:
    """Returns (company_name, jd_text)."""
    company = _company_from_url(job_url)
    async with stealth_page() as page:
        await page.goto(job_url, timeout=20_000, wait_until="domcontentloaded")

        # Try a few common JD containers
        jd_text = ""
        for sel in ["#content", "div[itemprop='description']", ".job__description", "section.application", "main"]:
            loc = page.locator(sel).first
            try:
                if await loc.count() > 0:
                    text = await loc.inner_text(timeout=2000)
                    if text and len(text) > 200:
                        jd_text = text.strip()
                        break
            except Exception:
                continue

        # Try to extract a more accurate company name from page chrome
        try:
            title = await page.title()
            # Greenhouse titles often look like "Job Title - Company - Greenhouse"
            for sep in [" at ", " - ", " | "]:
                if sep in title:
                    parts = title.split(sep)
                    if len(parts) >= 2:
                        candidate = parts[-1].strip().replace("Greenhouse", "").strip(" -|")
                        if candidate and 1 < len(candidate) < 50:
                            company = candidate
                            break
        except Exception:
            pass

    return company, jd_text


def _company_from_url(url: str) -> str:
    """Extract company slug from a Greenhouse URL."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path

    # job-boards.greenhouse.io/<company>/jobs/...
    # boards.greenhouse.io/<company>/jobs/...
    if "greenhouse.io" in host:
        segments = [s for s in path.split("/") if s]
        if segments:
            return segments[0].replace("-", " ").title()

    # company.com/careers/...?gh_jid=...
    if host:
        return host.replace("www.", "").split(".")[0].title()

    return "Unknown"
