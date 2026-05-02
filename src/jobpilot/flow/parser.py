# ============================================================================
# Copyright (c) 2026 Areej Ahmed. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Greenhouse form schema parser.

We do not rely on CSS class hashes (they regenerate). Instead we use:
  - Stable input names (job_application[first_name])
  - ARIA attributes (aria-required, aria-label)
  - Label-for-input pairing
  - Question text as the human-readable label fed to the LLM

Output is a list of FormField records that the orchestrator iterates over.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from playwright.async_api import Page


FieldKind = Literal[
    "text",
    "email",
    "tel",
    "url",
    "textarea",
    "select",
    "radio",
    "checkbox",
    "file",
    "unknown",
]


# Greenhouse standard fields → our payload keys
STANDARD_FIELD_MAP = {
    "job_application[first_name]": "first_name",
    "job_application[last_name]": "last_name",
    "job_application[email]": "email",
    "job_application[phone]": "phone",
    "job_application[location]": "location",
    "job_application[urls_attributes][0][value]": "linkedin",  # often LinkedIn URL slot 0
}

# Fields whose label contains these substrings are mapped (case-insensitive)
LABEL_KEYWORD_MAP = [
    (("linkedin",), "linkedin"),
    (("https://github.com/aa2149/jobpilot",), "https://github.com/aa2149/jobpilot"),
    (("portfolio", "personal website", "website"), "portfolio"),
    (("phone",), "phone"),
    (("first name",), "first_name"),
    (("last name", "family name", "surname"), "last_name"),
    (("email",), "email"),
    (("location", "city"), "location"),
]


@dataclass
class FormField:
    selector: str
    name: str | None
    kind: FieldKind
    label: str
    required: bool
    max_length: int | None
    is_question: bool = False
    payload_key: str | None = None  # mapping into Applicant
    is_honeypot: bool = False
    honeypot_reason: str | None = None


@dataclass
class FormSchema:
    fields: list[FormField] = field(default_factory=list)
    file_input_selector: str | None = None
    submit_button_selector: str | None = None
    jd_text: str = ""

    def standard_fields(self) -> list[FormField]:
        return [f for f in self.fields if f.payload_key and not f.is_honeypot]

    def open_questions(self) -> list[FormField]:
        return [f for f in self.fields if f.is_question and not f.is_honeypot]


async def parse_form(page: "Page") -> FormSchema:
    """Walk the page and extract a FormSchema. Honeypots are flagged but
    included so the orchestrator can log them.
    """
    from jobpilot.flow.honeypot import is_honeypot

    schema = FormSchema()

    # Job description text — Greenhouse uses #content, .job__description, or div[itemprop=description]
    for jd_selector in ["#content", "div[itemprop='description']", ".job__description", "section.application"]:
        loc = page.locator(jd_selector).first
        if await loc.count() > 0:
            try:
                text = await loc.inner_text(timeout=2000)
                if text and len(text) > 100:
                    schema.jd_text = text
                    break
            except Exception:
                continue

    # File input (resume)
    file_loc = page.locator("input[type='file']").first
    if await file_loc.count() > 0:
        schema.file_input_selector = "input[type='file']"

    # Submit button — Greenhouse standardizes on input[type=submit] or button[type=submit]
    for sub_sel in ["button[type='submit']", "input[type='submit']", "button#submit_app"]:
        if await page.locator(sub_sel).count() > 0:
            schema.submit_button_selector = sub_sel
            break

    # Iterate over inputs and textareas
    inputs = await page.locator("input, textarea, select").all()

    for idx, inp in enumerate(inputs):
        try:
            tag = await inp.evaluate("el => el.tagName.toLowerCase()")
            name = await inp.get_attribute("name")
            input_type = (await inp.get_attribute("type") or "").lower()
            aria_required = await inp.get_attribute("aria-required")
            required_attr = await inp.get_attribute("required")
            maxlen_attr = await inp.get_attribute("maxlength")

            # Skip submit/button inputs — those are not fields
            if input_type in ("submit", "button", "hidden", "reset"):
                continue
            # File handled separately
            if input_type == "file":
                continue

            # Build a stable selector: prefer name, fall back to nth-child position
            if name:
                selector = f"{tag}[name='{name}']"
            else:
                selector = f"{tag} >> nth={idx}"

            # Find the label
            label_text = await _resolve_label(inp, name)

            # Determine kind
            kind: FieldKind
            if tag == "textarea":
                kind = "textarea"
            elif tag == "select":
                kind = "select"
            elif input_type in ("text", "email", "tel", "url"):
                kind = input_type  # type: ignore[assignment]
            elif input_type == "radio":
                kind = "radio"
            elif input_type == "checkbox":
                kind = "checkbox"
            else:
                kind = "unknown"

            required = bool(required_attr) or aria_required == "true"
            max_length = int(maxlen_attr) if maxlen_attr and maxlen_attr.isdigit() else None

            # Open-ended question detection
            is_question = False
            if kind == "textarea":
                is_question = True
            elif kind == "text" and max_length and max_length > 200:
                is_question = True
            elif kind == "text" and label_text and any(k in label_text.lower() for k in ("describe", "tell us", "why", "how would")):
                is_question = True

            # Payload mapping
            payload_key = STANDARD_FIELD_MAP.get(name or "")
            if not payload_key and label_text:
                lower = label_text.lower()
                for keywords, key in LABEL_KEYWORD_MAP:
                    if any(kw in lower for kw in keywords):
                        payload_key = key
                        break

            # Honeypot check
            is_hp, hp_reason = await is_honeypot(page, inp)

            schema.fields.append(FormField(
                selector=selector,
                name=name,
                kind=kind,
                label=label_text,
                required=required,
                max_length=max_length,
                is_question=is_question,
                payload_key=payload_key,
                is_honeypot=is_hp,
                honeypot_reason=hp_reason,
            ))
        except Exception:
            # Don't fail the whole parse on one weird element
            continue

    return schema


async def _resolve_label(inp, name: str | None) -> str:
    """Best-effort label resolution: aria-label → label[for=id] → preceding label → name."""
    try:
        aria = await inp.get_attribute("aria-label")
        if aria:
            return aria.strip()

        input_id = await inp.get_attribute("id")
        if input_id:
            page = inp.page  # type: ignore[attr-defined]
            label_loc = page.locator(f"label[for='{input_id}']").first
            if await label_loc.count() > 0:
                text = await label_loc.inner_text(timeout=1000)
                if text:
                    return text.strip().rstrip("*").strip()

        # Walk up to find an enclosing label or fieldset legend
        label_text = await inp.evaluate(
            """
            (el) => {
                let cur = el;
                while (cur && cur !== document.body) {
                    if (cur.tagName === 'LABEL') return cur.textContent;
                    const lbl = cur.querySelector('label, legend');
                    if (lbl) return lbl.textContent;
                    cur = cur.parentElement;
                }
                return '';
            }
            """
        )
        if label_text:
            return str(label_text).strip().rstrip("*").strip()
    except Exception:
        pass

    return (name or "").replace("[", " ").replace("]", " ").strip()
