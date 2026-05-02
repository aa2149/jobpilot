# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Application settings loaded from environment / .env."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- LLM (Gemini only in v1) ----
    gemini_api_key: str | None = None
    llm_model: str = "gemini-2.0-flash"

    # ---- Browser ----
    headless: bool = True
    auto_submit: bool = True
    screenshot_on_failure: bool = True
    stealth_profile: Literal["patchright", "playwright_stealth"] = "patchright"
    proxy_url: str | None = None
    har_capture: bool = False

    # ---- Logging ----
    log_level: str = "info"

    # ---- Fit cache ----
    fit_cache_dir: Path = Path(".cache/fit")
    fit_cache_reviews_days: int = 30
    fit_cache_careers_days: int = 7

    # ---- Email (stubbed in v1 — see flow/email_stub.py) ----
    email_from: str = "noreply@jobpilot.local"
    email_enabled: bool = False  # If true, attempt real send via configured provider

    # ---- Project-relative paths ----
    project_root: Path = Field(default_factory=lambda: Path.cwd())

    @property
    def logs_dir(self) -> Path:
        path = self.project_root / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def has_gemini(self) -> bool:
        return bool(self.gemini_api_key)


settings = Settings()
