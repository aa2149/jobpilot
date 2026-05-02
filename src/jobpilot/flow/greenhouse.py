# ============================================================================
# Copyright (c) 2026 Areej Ahmed. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""The Greenhouse application flow.

This is the orchestrator. Given a job URL and applicant payload, drive a
real Greenhouse application form to the pre-submit state.

Each step is named, budgeted, and individually logged. Failures are
classified into structured error states (see api/schemas.py).
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

from jobpilot.api.schemas import Applicant, ApplyOptions, ApplyState
from jobpilot.browser.launcher import stealth_page
from jobpilot.flow.parser import FormField, FormSchema, parse_form
from jobpilot.flow.upload import upload_resume
from jobpilot.humanizer.pacing import human_scroll, micro_pause, occasional_scroll_back, section_pause
from jobpilot.humanizer.typing import human_type_locator
from jobpilot.llm.client import get_client
from jobpilot.llm.prompts import open_question_prompt
from jobpilot.observability.artifacts import capture_dom_snapshot, capture_screenshot
from jobpilot.observability.logger import get_run_logger, log_path


# Patterns in URLs / DOM that mean we hit bot detection
BOT_BLOCK_HINTS = [
    "cloudflare",
    "challenges.cloudflare.com",
    "hcaptcha",
    "are you human",
    "unusual activity",
    "verifying you are human",
]


@dataclass
class FlowResult:
    state: ApplyState
    fields_filled: int = 0
    questions_answered: int = 0
    resume_uploaded: bool = False
    screenshot: str | None = None
    reason: str | None = None
    step: str | None = None


async def run_apply(
    *,
    run_id: str,
    job_url: str,
    applicant: Applicant,
    options: ApplyOptions,
) -> FlowResult:
    """Top-level entry point. Returns a FlowResult with structured outcome."""
    log = get_run_logger(run_id)
    log.info("flow.start", job_url=job_url, applicant_email=applicant.email)

    started = time.monotonic()

    try:
        async with stealth_page() as page:
            # ---- 1. NAVIGATE ----
            log.info("step.start", step="navigate")
            try:
                await page.goto(job_url, timeout=20_000, wait_until="domcontentloaded")
            except Exception as e:
                return _fail("job_not_found", f"navigation failed: {e}", "navigate", run_id, log)

            if await _detect_block(page):
                shot = await _safe_screenshot(page, run_id, "failure")
                return _fail("blocked_by_bot_detection", "challenge page detected after navigate", "navigate", run_id, log, screenshot=shot)

            # Wait for form to materialize.
            # Some Greenhouse pages (Grammarly, Thumbtack) render the application
            # form via a second XHR after the initial HTML loads. We:
            #   1. Wait for networkidle to let JS finish its work.
            #   2. Scroll down to trigger any lazy-render logic.
            #   3. Try to click an Apply button if the form is behind one.
            #   4. Wait up to 15s for any input/textarea to appear.
            try:
                await page.wait_for_load_state("networkidle", timeout=12_000)
            except Exception:
                pass  # networkidle can time out on pages with polling — that's fine

            # Scroll down to trigger lazy-render / reveal the application section
            await page.evaluate("window.scrollBy(0, 600)")
            await asyncio.sleep(1.2)

            # Wait for form to materialize (Greenhouse is largely SSR but some embeds are async)
            try:
                await page.wait_for_selector("input, textarea", timeout=15_000)
            except Exception:
                pass

            # Some Greenhouse pages render the form on a separate "Apply" button click
            await _maybe_click_apply_button(page)

            # Give the form a moment to finish rendering after the Apply click
            await asyncio.sleep(0.8)

            # ---- 2. PARSE FORM ----
            log.info("step.start", step="parse_form")
            schema = await parse_form(page)
            log.info(
                "form.parsed",
                fields=len(schema.fields),
                questions=len(schema.open_questions()),
                honeypots=sum(1 for f in schema.fields if f.is_honeypot),
                has_file_input=bool(schema.file_input_selector),
            )
            if len(schema.fields) == 0:
                shot = await _safe_screenshot(page, run_id, "failure")
                await capture_dom_snapshot(page, run_id, "dom_snapshot")
                return _fail("form_schema_unrecognized", "no fields detected", "parse_form", run_id, log, screenshot=shot)

            await section_pause()

            # ---- 4. FILL BASICS (skip 3=score for now; orchestrator does it upstream) ----
            log.info("step.start", step="fill_basics")
            fields_filled = 0
            for field_obj in schema.standard_fields():
                if field_obj.is_question:
                    continue
                value = _value_for_field(field_obj, applicant)
                if not value:
                    if field_obj.required:
                        log.warning("field.required_no_value", label=field_obj.label, payload_key=field_obj.payload_key)
                    continue
                try:
                    await _fill_one_field(page, field_obj, value)
                    fields_filled += 1
                    log.info("field.filled", label=field_obj.label, kind=field_obj.kind)
                except Exception as e:
                    log.warning("field.fill_failed", label=field_obj.label, error=str(e))

            await occasional_scroll_back(page)
            await section_pause()

            # ---- 5. UPLOAD RESUME ----
            resume_uploaded = False
            if schema.file_input_selector:
                log.info("step.start", step="upload_resume")
                try:
                    await upload_resume(page, schema.file_input_selector, applicant.resume_path)
                    resume_uploaded = True
                    log.info("resume.uploaded", path=applicant.resume_path)
                except FileNotFoundError as e:
                    return _fail("upload_failed", f"resume not found: {e}", "upload_resume", run_id, log)
                except Exception as e:
                    log.warning("resume.upload_failed", error=str(e))
                    return _fail("upload_failed", f"upload failed: {e}", "upload_resume", run_id, log)
                await section_pause()

            # ---- 6. ANSWER OPEN QUESTIONS ----
            log.info("step.start", step="answer_questions")
            questions_answered = 0
            llm = get_client(options.llm_model)
            for q_idx, q_field in enumerate(schema.open_questions()):
                # Skip the questions we'd map to standard fields (cover letter would be here)
                # Heuristic: if max_length is small (< 200) AND label matches a standard, skip
                max_chars = q_field.max_length or 1500
                try:
                    system, user = open_question_prompt(
                        resume_text=applicant.resume_text,
                        jd_text=schema.jd_text or "(JD text unavailable)",
                        question_text=q_field.label,
                        max_chars=max_chars,
                    )
                    log.info("llm.call.start", question_index=q_idx, max_chars=max_chars)
                    answer = await llm.complete(system, user, max_tokens=900)
                    if not answer:
                        log.warning("llm.empty_answer", question=q_field.label)
                        continue
                    # Type into the textarea/input
                    locator = page.locator(q_field.selector).first
                    await human_type_locator(locator, answer)
                    questions_answered += 1
                    log.info("question.answered", index=q_idx, chars=len(answer))
                except Exception as e:
                    log.warning("question.failed", index=q_idx, error=str(e))
                    # Best-effort: keep going. Don't fail the whole run on one question.
                    continue
                await human_scroll(page)
                await micro_pause()

            # ---- 8. VALIDATE FORM (lightweight: re-check required fields) ----
            log.info("step.start", step="validate_form")
            # We re-parse to catch any new required fields revealed by interaction
            schema2 = await parse_form(page)
            missing = []
            for f in schema2.fields:
                if not f.required or f.is_honeypot:
                    continue
                try:
                    loc = page.locator(f.selector).first
                    val = await loc.input_value(timeout=1500) if f.kind in ("text", "email", "tel", "url", "textarea") else ""
                    if not val:
                        missing.append(f.label)
                except Exception:
                    pass
            if missing:
                log.warning("validate.required_missing", fields=missing[:10])

            # ---- 9. HALT OR SUBMIT ----
            shot_path = await _safe_screenshot(page, run_id, "pre_submit")

            if not options.auto_submit:
                log.info("flow.halted_pre_submit", screenshot=str(shot_path), duration_ms=int((time.monotonic() - started) * 1000))
                return FlowResult(
                    state="pre_submit_ready",
                    fields_filled=fields_filled,
                    questions_answered=questions_answered,
                    resume_uploaded=resume_uploaded,
                    screenshot=str(shot_path) if shot_path else None,
                )

            # Auto-submit
            if not schema.submit_button_selector:
                return _fail("unknown_error", "auto_submit set but submit button not found", "halt_or_submit", run_id, log, screenshot=str(shot_path))

            log.info("step.start", step="submit")
            await page.locator(schema.submit_button_selector).first.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=15_000)
            except Exception:
                pass
            log.info("flow.submitted")
            return FlowResult(
                state="submitted",
                fields_filled=fields_filled,
                questions_answered=questions_answered,
                resume_uploaded=resume_uploaded,
                screenshot=str(shot_path) if shot_path else None,
            )

    except asyncio.TimeoutError:
        return _fail("timeout", "operation exceeded budget", "unknown", run_id, log)
    except Exception as e:
        log.exception("flow.unhandled_error", error=str(e))
        return _fail("unknown_error", f"{type(e).__name__}: {e}", "unknown", run_id, log)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _value_for_field(field_obj: FormField, applicant: Applicant) -> str:
    """Pluck the right value off the Applicant for this field's payload_key."""
    if not field_obj.payload_key:
        return ""
    val = getattr(applicant, field_obj.payload_key, None)
    return str(val) if val else ""


async def _fill_one_field(page, field_obj: FormField, value: str) -> None:
    locator = page.locator(field_obj.selector).first
    if field_obj.kind in ("text", "email", "tel", "url", "textarea"):
        # Try normal human-type first; if the element isn't scrollable into view
        # (e.g. a phone field hidden behind an overlay on some Greenhouse embeds)
        # fall back to a JS-based fill so we don't stall for 30 seconds.
        try:
            await human_type_locator(locator, value)
        except Exception:
            try:
                await locator.evaluate(
                    "(el, v) => { el.value = v; el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); }",
                    value,
                )
            except Exception:
                raise  # re-raise so caller can log warning
    elif field_obj.kind == "select":
        await locator.select_option(value=value)
    elif field_obj.kind == "checkbox":
        if value.lower() in ("true", "1", "yes"):
            await locator.check()


async def _maybe_click_apply_button(page) -> None:
    """Some Greenhouse-embedded postings hide the form behind an Apply button."""
    for sel in ["a:has-text('Apply for this Job')", "button:has-text('Apply')", "a:has-text('Apply now')"]:
        loc = page.locator(sel).first
        try:
            if await loc.count() > 0 and await loc.is_visible(timeout=500):
                await loc.click()
                await page.wait_for_load_state("domcontentloaded", timeout=8000)
                return
        except Exception:
            continue


async def _detect_block(page) -> bool:
    try:
        url = page.url.lower()
        if any(h in url for h in ("/cdn-cgi/challenge-platform", "/challenge")):
            return True
        title = (await page.title()).lower()
        if any(h in title for h in BOT_BLOCK_HINTS):
            return True
        body_text = ""
        try:
            body_text = (await page.locator("body").inner_text(timeout=1500)).lower()
        except Exception:
            pass
        return any(h in body_text for h in BOT_BLOCK_HINTS)
    except Exception:
        return False


async def _safe_screenshot(page, run_id: str, name: str):
    try:
        return await capture_screenshot(page, run_id, name)
    except Exception:
        return None


def _fail(state: ApplyState, reason: str, step: str, run_id: str, log, screenshot=None) -> FlowResult:
    log.error("flow.failed", state=state, reason=reason, step=step)
    return FlowResult(
        state=state,
        reason=reason,
        step=step,
        screenshot=str(screenshot) if screenshot else None,
    )
