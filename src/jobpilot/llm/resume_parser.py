# ============================================================================
# Copyright (c) 2026 Areej Ahmed. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Resume auto-parser.

Takes a PDF, extracts text, sends it to Gemini with a structured-output
prompt, and returns parsed applicant fields. Used by POST /parse-resume.

PDF text extraction uses pdfplumber (best accuracy for two-column and
designed resumes) with PyPDF2 as fallback.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jobpilot.llm.client import get_client


PARSE_SYSTEM = """\
You are a resume parser. Given the raw text extracted from a PDF resume,
extract structured applicant information.

Rules:
- Extract ONLY what is explicitly present in the text. Do not invent data.
- For fields that are not found, use null.
- For email, phone, LinkedIn, GitHub, portfolio: look for URLs, @-addresses,
  phone number patterns.
- For location: look for city/country mentions near the name/header.
- For work_auth: look for visa status, work authorization mentions. If not
  mentioned, return null.
- Return the FULL resume text (cleaned up, readable) in the resume_text field.
  This is what the LLM uses later when answering open-ended application questions.

Output a single JSON object with these exact keys:
{
  "first_name": "string or null",
  "last_name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "location": "string or null",
  "linkedin": "URL string or null",
  "github": "URL string or null",
  "portfolio": "URL string or null",
  "work_auth": "string or null",
  "resume_text": "the full cleaned resume text"
}
"""


async def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes. Tries pdfplumber first, falls back to PyPDF2."""
    text = ""

    # Try pdfplumber (best for designed resumes)
    try:
        import pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
            text = "\n\n".join(pages)
    except Exception:
        pass

    # Fallback: PyPDF2
    if not text.strip():
        try:
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(pdf_bytes))
            pages = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)
            text = "\n\n".join(pages)
        except Exception:
            pass

    if not text.strip():
        raise ValueError("Could not extract text from the uploaded PDF. Is it a scanned image? Try a text-based PDF.")

    return text


async def parse_resume_text(raw_text: str) -> dict[str, Any]:
    """Send extracted text to Gemini and get structured fields back."""
    client = get_client()

    # Truncate if extremely long (some resumes are 10+ pages)
    truncated = raw_text[:12000] if len(raw_text) > 12000 else raw_text

    user_prompt = f"RESUME TEXT:\n\n{truncated}"

    parsed = await client.complete_json(PARSE_SYSTEM, user_prompt, max_tokens=2000)

    # Ensure all expected keys exist (in case Gemini omits some)
    defaults = {
        "first_name": None,
        "last_name": None,
        "email": None,
        "phone": None,
        "location": None,
        "linkedin": None,
        "github": None,
        "portfolio": None,
        "work_auth": None,
        "resume_text": raw_text,  # fallback to raw if Gemini doesn't clean it
    }

    for key, default in defaults.items():
        if key not in parsed or parsed[key] is None:
            parsed[key] = default

    # Always use the full raw text as resume_text (Gemini sometimes truncates)
    if not parsed.get("resume_text") or len(parsed["resume_text"]) < len(raw_text) * 0.5:
        parsed["resume_text"] = raw_text

    return parsed


async def parse_resume_pdf(pdf_bytes: bytes) -> dict[str, Any]:
    """End-to-end: PDF bytes → extracted text → structured fields."""
    raw_text = await extract_text_from_pdf(pdf_bytes)
    parsed = await parse_resume_text(raw_text)
    return parsed
