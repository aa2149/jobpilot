# ============================================================================
# Copyright (c) 2026 Areej Ahmed. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Structured JSON logger via structlog.

Each run gets its own JSONL file at logs/<run_id>/run.jsonl. The logger is
bound with the run_id so every event in that run is correlated.
"""
from __future__ import annotations

import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from jobpilot.config import settings


def make_run_id() -> str:
    """Format: run_2026-05-01T09-12-44Z_8f3a"""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    short = uuid.uuid4().hex[:4]
    return f"run_{ts}_{short}"


def run_dir(run_id: str) -> Path:
    path = settings.logs_dir / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def configure(level: str | None = None) -> None:
    """Configure structlog once. Idempotent."""
    log_level = getattr(logging, (level or settings.log_level).upper(), logging.INFO)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        cache_logger_on_first_use=True,
    )


def get_run_logger(run_id: str) -> structlog.BoundLogger:
    """Get a logger bound to a run_id and tee'd to logs/<run_id>/run.jsonl."""
    configure()
    file_path = run_dir(run_id) / "run.jsonl"
    handler = logging.FileHandler(file_path, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter("%(message)s"))

    py_logger = logging.getLogger(f"jobpilot.run.{run_id}")
    # Avoid double-handlers on hot reload
    if not any(isinstance(h, logging.FileHandler) and getattr(h, "baseFilename", "") == str(file_path) for h in py_logger.handlers):
        py_logger.addHandler(handler)
    py_logger.setLevel(logging.DEBUG)
    py_logger.propagate = True

    return structlog.get_logger(f"jobpilot.run.{run_id}").bind(run_id=run_id)


def log_path(run_id: str) -> Path:
    return run_dir(run_id) / "run.jsonl"
