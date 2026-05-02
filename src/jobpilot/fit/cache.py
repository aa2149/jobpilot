# ============================================================================
# Copyright (c) 2026 Areej Ahmed. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Disk-backed cache for fit-intelligence sources.

Glassdoor reviews are expensive (each scrape is several seconds and risks
detection). Cache aggressively: 30 days for reviews, 7 for careers pages.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from jobpilot.config import settings


def _cache_dir() -> Path:
    path = settings.fit_cache_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def _key(namespace: str, *parts: str) -> Path:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return _cache_dir() / namespace / f"{digest}.json"


def get(namespace: str, *parts: str, ttl_days: int) -> tuple[Any, int] | None:
    """Returns (value, age_days) if hit, else None."""
    path = _key(namespace, *parts)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        cached_at = data.get("cached_at", 0)
        age_seconds = time.time() - cached_at
        age_days = int(age_seconds / 86400)
        if age_days > ttl_days:
            return None
        return data["value"], age_days
    except Exception:
        return None


def put(namespace: str, value: Any, *parts: str) -> None:
    path = _key(namespace, *parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"cached_at": time.time(), "value": value}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
