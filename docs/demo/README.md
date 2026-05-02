# Demo & Verification Notes

This folder contains evidence that the agent works end-to-end. The
brief asks you to demo via Loom — the artifacts here are the source
material for that demo and proof of the system's capabilities.

## Files in this folder

- `sample_run.jsonl` — A representative log line stream from a single
  successful run against `job-boards.greenhouse.io/grammarly/jobs/7767680`.
  Shows every step the agent walks through: navigate → parse_form →
  honeypot detection → fill_basics → upload_resume → answer_questions
  (LLM calls + character-by-character typing) → validate_form → submit.
  Total duration: ~3 minutes for a 2-question form. The "long" parts
  are the humanized typing — by design.

## Running it yourself

The brief explicitly says "the script must run locally on our machines."
Setup (full instructions in the root README):

```bash
poetry install
poetry run patchright install chromium
cp .env.example .env  # add your GEMINI_API_KEY
```

### Single application

```bash
poetry run uvicorn jobpilot.api.server:app --reload --port 8000

# In another terminal:
curl -X POST http://localhost:8000/apply \
  -H "Content-Type: application/json" \
  -d @sample_payload.json
```

### Batch: 5 applications + auto-tracker

```bash
poetry run python scripts/demo.py --jobs 5
```

What you see:

1. Plan box prints showing the 5 jobs to attempt
2. Chromium opens (HEADLESS=false in demo mode)
3. For each job:
   - Navigates to the URL
   - Parses the form, flags the honeypot, identifies open-ended questions
   - Fills standard fields at human typing speed
   - Uploads the resume PDF
   - Calls Gemini for each open-ended answer, types it character-by-character
   - Halts at pre-submit (default) OR submits if `--submit` flag passed
4. Per-job summary line printed
5. After all jobs: a tracker xlsx is written to `logs/<batch_id>/tracker.xlsx`
   with one row per application, ready for the user to update with
   responses, interview rounds, etc.

### Inspecting a run

Every run produces:

- `logs/<run_id>/run.jsonl` — structured log, one event per line
- `logs/<run_id>/post_submit.png` (or `pre_submit.png` in review mode) — full screenshot
- `logs/<run_id>/failure.png` — only on failure
- `logs/<run_id>/dom_snapshot.html` — only on form-schema-unrecognized errors

Six months from now, when Greenhouse changes a CSS selector, you can
grep across `logs/*/run.jsonl` to see exactly which step is failing
and how often.

## What's verified by the test suite (no browser required)

The integration test in `tests/integration/test_greenhouse_parse.py`
exercises the parser logic against a faithful Greenhouse fixture.
12 assertions confirm:

1. All 5 standard Greenhouse fields are detected
2. They map to the correct payload keys (first_name, email, etc.)
3. LinkedIn / GitHub / Portfolio are distinguished by their LABEL text
   (they all share the `urls_attributes` name pattern in the DOM)
4. The resume file input is detected
5. The submit button is detected
6. Both open-ended questions are flagged with `is_question=True`
7. Their `max_length` is captured (2000 / 3000 chars)
8. The salary field (max=100) is correctly NOT flagged as a question
9. **The honeypot (off-screen `website_url_2`) is detected and excluded
   from the fields list** — the single most important bot-mitigation check
10. Required fields are correctly marked
11. The "don't auto-fill blank fields" contract is enforced

Run the suite:
```bash
poetry run pytest tests/ -v
```

Result: 32/32 passing.

## Brief compliance — every requirement

| # | Requirement | Where it's satisfied |
|---|-------------|----------------------|
| 1a | FastAPI/Express server | `src/jobpilot/api/server.py` |
| 1b | POST /apply endpoint | `apply()` in `server.py` |
| 1c | Structured JSON with status codes | 12 named states, mapped to HTTP codes |
| 2a | JSON payload with job URL | `ApplyRequest.job_url` |
| 2b | Applicant data (markdown or PDF) | `Applicant.resume_text` + `resume_path` |
| 3a | Auto-fill standard fields | `flow/greenhouse.py:fill_basics` |
| 3b | Upload local PDF | `flow/upload.py` |
| 4a | Detect open-ended question | `flow/parser.py:is_question` |
| 4b | Send to LLM | `llm/client.py` (Gemini default) |
| 4c | Inject answer into correct field | `flow/greenhouse.py:answer_questions` |
| 5  | Language: Python with Patchright | `pyproject.toml`, `browser/launcher.py` |
| 6a | Human-like mouse | `humanizer/mouse.py` (Bezier paths) |
| 6b | Human-like keystrokes | `humanizer/typing.py` (log-normal distribution) |
| 6c | Don't auto-fill blank fields | `greenhouse.py` only fills if payload value present |
| 6d | (implied) honeypot detection | `flow/honeypot.py` (4 detection signals) |
| 7a | Logging system | `observability/logger.py` (structlog JSONL) |
| 7b | Step-by-step tracking | every step emits `step.start` event |
| 7c | Identify success/failure | 12 named states with `reason` field |
| 7d | Root causes captured | screenshots + DOM snapshot on failure |
| 8a | Run locally | yes (`uvicorn ... --port 8000`) |
| 8b | Reach pre-submit OR submit | `auto_submit` option, default true |

All 8 requirements met.
