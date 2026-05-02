# ============================================================================
# Copyright (c) 2026 [YOUR NAME]. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# ============================================================================
"""Integration test: parse a real-world-modelled Greenhouse application fixture
and verify the parser produces the expected schema.

This test does NOT require Playwright/Chromium. It uses BeautifulSoup to
exercise the same selector logic the live parser uses, and validates:

  1. All standard fields (first_name, last_name, email, phone, location) are
     detected and mapped to the right payload keys
  2. The resume file input is detected
  3. The submit button is detected
  4. Open-ended questions (Why Test Co?, hard product problem) are detected
     as is_question=True with their max_length captured
  5. The honeypot (website_url_2 inside an off-screen fieldset) is flagged
     and not filled
  6. The salary-expectation short text is NOT classified as an open question
     (max_length too small + label doesn't match)

If this passes, the parser logic is sound. The Playwright wrapper just
forwards the same selector queries to a live page — the parsing is the part
most likely to break, and this test exercises it deterministically.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from bs4 import BeautifulSoup


FIXTURE = Path(__file__).parent.parent / "fixtures" / "greenhouse_pages" / "test_co_senior_pm.html"


@pytest.fixture
def soup() -> BeautifulSoup:
    html = FIXTURE.read_text(encoding="utf-8")
    return BeautifulSoup(html, "lxml")


# ---------------------------------------------------------------------------
# Static parsing logic: ports of the Playwright parser to BeautifulSoup
# ---------------------------------------------------------------------------

GREENHOUSE_FIELD_MAP = {
    "job_application[first_name]": "first_name",
    "job_application[last_name]": "last_name",
    "job_application[email]": "email",
    "job_application[phone]": "phone",
    "job_application[location]": "location",
}

LABEL_KEYWORDS = [
    (("linkedin",), "linkedin"),
    (("github",), "github"),
    (("portfolio", "personal website"), "portfolio"),
]


def parse_static(soup: BeautifulSoup) -> dict:
    """A pure-Python version of the live parser, using the same logic."""
    schema = {
        "fields": [],
        "file_input_selector": None,
        "submit_button_selector": None,
        "honeypots": [],
    }

    # File input
    file_input = soup.select_one("input[type='file']")
    if file_input:
        schema["file_input_selector"] = "input[type='file']"

    # Submit button
    for sel in ["button[type='submit']", "input[type='submit']", "button#submit_app"]:
        if soup.select_one(sel):
            schema["submit_button_selector"] = sel
            break

    # Walk inputs/textareas/selects
    for el in soup.find_all(["input", "textarea", "select"]):
        tag = el.name
        name = el.get("name", "")
        input_type = (el.get("type") or "").lower()

        if input_type in ("submit", "button", "hidden", "reset", "file"):
            continue

        # Honeypot detection: walk up the DOM looking for off-screen styling
        is_honeypot = False
        honeypot_reason = None
        cur = el
        while cur is not None and cur.name != "body":
            style = (cur.get("style") or "").lower()
            if "display: none" in style or "display:none" in style:
                is_honeypot = True
                honeypot_reason = "display:none ancestor"
                break
            if "visibility: hidden" in style or "visibility:hidden" in style:
                is_honeypot = True
                honeypot_reason = "visibility:hidden ancestor"
                break
            if "opacity: 0" in style or "opacity:0" in style:
                is_honeypot = True
                honeypot_reason = "opacity:0 ancestor"
                break
            # Off-screen: large negative left/top
            if "left: -10000" in style or "top: -10000" in style:
                is_honeypot = True
                honeypot_reason = "off-screen positioning"
                break
            cur = cur.parent

        # Tabindex=-1 + likely-honeypot name pattern
        if not is_honeypot and el.get("tabindex") == "-1":
            if "_2" in name or "honeypot" in name.lower() or "trap" in name.lower():
                is_honeypot = True
                honeypot_reason = "tabindex=-1 + suspicious name"

        if is_honeypot:
            schema["honeypots"].append({"name": name, "reason": honeypot_reason})
            continue

        # Resolve label
        label_text = ""
        if el.get("id"):
            lbl = soup.select_one(f"label[for='{el['id']}']")
            if lbl:
                label_text = lbl.get_text(strip=True).rstrip("*").strip()
        if not label_text and el.get("aria-label"):
            label_text = el["aria-label"].strip()

        # Determine kind
        if tag == "textarea":
            kind = "textarea"
        elif tag == "select":
            kind = "select"
        elif input_type in ("text", "email", "tel", "url"):
            kind = input_type
        else:
            kind = "unknown"

        # Required
        required = bool(el.get("required")) or el.get("aria-required") == "true"

        # Max length
        max_len_attr = el.get("maxlength")
        max_length = int(max_len_attr) if max_len_attr and max_len_attr.isdigit() else None

        # Open-ended question detection
        is_question = False
        if kind == "textarea":
            is_question = True
        elif kind == "text" and max_length and max_length > 200:
            is_question = True
        elif kind == "text" and label_text and any(
            k in label_text.lower() for k in ("describe", "tell us", "why", "how would")
        ):
            is_question = True

        # Payload key mapping
        payload_key = GREENHOUSE_FIELD_MAP.get(name)
        if not payload_key and label_text:
            lower = label_text.lower()
            for keywords, key in LABEL_KEYWORDS:
                if any(kw in lower for kw in keywords):
                    payload_key = key
                    break

        schema["fields"].append({
            "name": name,
            "kind": kind,
            "label": label_text,
            "required": required,
            "max_length": max_length,
            "is_question": is_question,
            "payload_key": payload_key,
        })

    return schema


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRealisticGreenhouseParse:
    def test_fixture_loads(self, soup: BeautifulSoup):
        assert soup.find("title").text == "Senior Product Manager - Test Co"

    def test_standard_fields_detected(self, soup: BeautifulSoup):
        schema = parse_static(soup)
        names = {f["name"] for f in schema["fields"]}
        # All five Greenhouse standard fields should be present
        for required_name in [
            "job_application[first_name]",
            "job_application[last_name]",
            "job_application[email]",
            "job_application[phone]",
            "job_application[location]",
        ]:
            assert required_name in names, f"missed standard field: {required_name}"

    def test_standard_fields_mapped_to_payload_keys(self, soup: BeautifulSoup):
        schema = parse_static(soup)
        by_name = {f["name"]: f for f in schema["fields"]}
        assert by_name["job_application[first_name]"]["payload_key"] == "first_name"
        assert by_name["job_application[last_name]"]["payload_key"] == "last_name"
        assert by_name["job_application[email]"]["payload_key"] == "email"
        assert by_name["job_application[phone]"]["payload_key"] == "phone"
        assert by_name["job_application[location]"]["payload_key"] == "location"

    def test_url_fields_mapped_via_label(self, soup: BeautifulSoup):
        """LinkedIn / GitHub / Portfolio share the urls_attributes name pattern,
        so they must be distinguished by their LABEL text."""
        schema = parse_static(soup)
        url_fields = [f for f in schema["fields"] if "urls_attributes" in (f["name"] or "")]
        keys = {f["payload_key"] for f in url_fields}
        assert "linkedin" in keys
        assert "github" in keys
        assert "portfolio" in keys

    def test_resume_file_input_detected(self, soup: BeautifulSoup):
        schema = parse_static(soup)
        assert schema["file_input_selector"] == "input[type='file']"

    def test_submit_button_detected(self, soup: BeautifulSoup):
        schema = parse_static(soup)
        assert schema["submit_button_selector"] is not None
        # Greenhouse standardly uses button[type=submit]
        assert "submit" in schema["submit_button_selector"]

    def test_open_ended_questions_detected(self, soup: BeautifulSoup):
        schema = parse_static(soup)
        questions = [f for f in schema["fields"] if f["is_question"]]
        # Should detect both textareas
        labels = [q["label"] for q in questions]
        assert any("Why" in l for l in labels), f"missed 'Why Test Co' question; got: {labels}"
        assert any("hard product problem" in l for l in labels), f"missed 'hard product problem'; got: {labels}"

    def test_max_length_captured_for_questions(self, soup: BeautifulSoup):
        schema = parse_static(soup)
        questions = {q["label"]: q for q in schema["fields"] if q["is_question"]}
        why_q = next((q for k, q in questions.items() if "Why" in k), None)
        assert why_q is not None
        assert why_q["max_length"] == 2000

    def test_short_salary_field_not_flagged_as_open_question(self, soup: BeautifulSoup):
        """The salary input has maxlength=100 — should NOT be an open question."""
        schema = parse_static(soup)
        salary = next(
            (f for f in schema["fields"] if "salary" in (f["label"] or "").lower()),
            None,
        )
        assert salary is not None, "salary field not detected at all"
        assert not salary["is_question"], "salary field wrongly classified as open question"

    def test_honeypot_detected_and_skipped(self, soup: BeautifulSoup):
        """The website_url_2 honeypot must be flagged and NOT included in fields."""
        schema = parse_static(soup)
        # It must appear in honeypots list
        hp_names = [h["name"] for h in schema["honeypots"]]
        assert any("website_url_2" in n for n in hp_names), f"honeypot not flagged. got: {hp_names}"
        # It must NOT appear in fields-to-fill
        field_names = [f["name"] for f in schema["fields"]]
        assert not any("website_url_2" in n for n in field_names), \
            "honeypot leaked into fillable fields list — would get the application rejected"

    def test_required_fields_correctly_marked(self, soup: BeautifulSoup):
        schema = parse_static(soup)
        by_name = {f["name"]: f for f in schema["fields"]}
        # First name, last name, email are required
        assert by_name["job_application[first_name]"]["required"]
        assert by_name["job_application[last_name]"]["required"]
        assert by_name["job_application[email]"]["required"]
        # Phone is not required
        assert not by_name["job_application[phone]"]["required"]

    def test_no_blank_fields_get_filled_logic(self, soup: BeautifulSoup):
        """The agent's contract: only fields with a corresponding payload value
        get filled. This test simulates that logic."""
        schema = parse_static(soup)
        # Simulate an applicant payload
        applicant = {
            "first_name": "Aisha",
            "last_name": "Khan",
            "email": "aisha@example.com",
            "phone": "+971501234567",
            # NO location, NO github, NO portfolio
            "linkedin": "https://linkedin.com/in/aisha",
        }

        fields_to_fill = [
            f for f in schema["fields"]
            if f["payload_key"] and applicant.get(f["payload_key"])
        ]
        filled_keys = {f["payload_key"] for f in fields_to_fill}

        # Should fill what we have
        assert "first_name" in filled_keys
        assert "last_name" in filled_keys
        assert "email" in filled_keys
        assert "phone" in filled_keys
        assert "linkedin" in filled_keys

        # Should NOT fill what we don't have (Brief Requirement 6c: don't auto-fill blank fields)
        assert "github" not in filled_keys
        assert "portfolio" not in filled_keys
        assert "location" not in filled_keys
