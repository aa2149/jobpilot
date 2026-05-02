# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Honeypot detection.

Honeypots are hidden inputs that humans cannot see and bots will
dutifully fill. Filling one is the fastest way to get an application
silently dropped.

A field is flagged as honeypot if any are true:
  - display:none, visibility:hidden, or opacity:0 on input or any ancestor
  - Off-screen positioning (negative coords, or width/height of 0)
  - tabindex="-1" and not part of the visible label structure
  - Field name matches a known honeypot pattern
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page


KNOWN_HONEYPOT_NAMES = {
    "website_url_2",
    "address_secondary",
    "url_2",
    "homepage",
    "honeypot",
    "trap",
    "bot_check",
}


async def is_honeypot(page: "Page", locator: "Locator") -> tuple[bool, str | None]:
    """Returns (is_honeypot, reason). Reason is None if not a honeypot."""
    try:
        # Check field name against known list
        name = await locator.get_attribute("name") or ""
        if name.lower() in KNOWN_HONEYPOT_NAMES:
            return True, f"name matches known honeypot pattern: {name}"

        # Check tabindex
        tabindex = await locator.get_attribute("tabindex")
        if tabindex == "-1":
            # Acceptable for some genuine fields, so we add the visibility check
            visible = await locator.is_visible()
            if not visible:
                return True, "tabindex=-1 and not visible"

        # Check visibility chain via JS
        result = await locator.evaluate(
            """
            (el) => {
                let cur = el;
                while (cur && cur !== document.body) {
                    const cs = window.getComputedStyle(cur);
                    if (cs.display === 'none') return {hidden: true, reason: 'display:none'};
                    if (cs.visibility === 'hidden') return {hidden: true, reason: 'visibility:hidden'};
                    if (parseFloat(cs.opacity) === 0) return {hidden: true, reason: 'opacity:0'};
                    cur = cur.parentElement;
                }
                const r = el.getBoundingClientRect();
                if (r.width === 0 || r.height === 0) return {hidden: true, reason: 'zero size'};
                if (r.left < -1000 || r.top < -1000) return {hidden: true, reason: 'off-screen'};
                return {hidden: false};
            }
            """
        )
        if result and result.get("hidden"):
            return True, str(result.get("reason"))

        return False, None
    except Exception:
        # Best-effort: if we can't tell, default to safe (treat as non-honeypot
        # but log upstream).
        return False, None
