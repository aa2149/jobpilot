# ============================================================================
# Copyright (c) 2026 [Areej Ahmed]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Gemini LLM client.

JobPilot v1 uses Google Gemini exclusively. The free tier (15 RPM,
1M tokens/day) is sufficient for a single applicant running batches of
up to ~50 applications/day. Get a key at:
https://aistudio.google.com/apikey

The flow/ and fit/ modules call `complete()` and `complete_json()`
without knowing the underlying provider — if a future version wants to
add Claude or GPT, it would extend an abstract base class here.
"""
from __future__ import annotations

import json
from typing import Any

from jobpilot.config import settings


class GeminiClient:
    """Google Gemini via the google-generativeai SDK."""

    def __init__(self, api_key: str, model: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model

    async def complete(self, system: str, user: str, *, max_tokens: int = 1024) -> str:
        model = self._genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=system,
        )
        resp = await model.generate_content_async(
            user,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": 0.7,
            },
        )
        return (resp.text or "").strip()

    async def complete_json(self, system: str, user: str, *, max_tokens: int = 1024) -> dict[str, Any]:
        json_system = system + (
            "\n\nReturn a single JSON object. Output must be parseable by json.loads(). "
            "Do not wrap in markdown fences. Do not include any prose before or after the JSON."
        )
        model = self._genai.GenerativeModel(
            model_name=self._model_name,
            system_instruction=json_system,
        )
        resp = await model.generate_content_async(
            user,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": 0.4,
                "response_mime_type": "application/json",
            },
        )
        return _parse_json(resp.text or "{}")


def _parse_json(raw: str) -> dict[str, Any]:
    """Tolerate ```json fences and stray prose around a JSON object."""
    text = raw.strip()
    if text.startswith("```"):
        parts = text.split("```", 2)
        if len(parts) >= 2:
            block = parts[1]
            if block.startswith("json"):
                block = block[4:]
            text = block.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}\nRaw: {raw[:500]}")


def get_client(model: str | None = None) -> GeminiClient:
    """Factory. Reads GEMINI_API_KEY from settings."""
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is required. Get one free at "
            "https://aistudio.google.com/apikey and add it to .env"
        )
    m = model or settings.llm_model
    return GeminiClient(settings.gemini_api_key, m)
