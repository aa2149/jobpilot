#!/usr/bin/env python3
# ============================================================================
# Copyright (c) 2026 Areej Ahmed. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# ============================================================================
"""End-to-end demo runner.

Runs the JobPilot agent against a curated set of real Greenhouse postings
from the brief's sample list. Captures full logs, screenshots, and a
personalized tracker.

USAGE:
    poetry run python scripts/demo.py
        Apply to 5 jobs from the brief's sample list using the default
        applicant in samples/demo_applicant.json. Stops at pre-submit
        (auto_submit=false in the demo script — does NOT submit during
        the demo run by default to avoid creating real applications).

    poetry run python scripts/demo.py --submit
        Same as above but auto_submit=true. ONLY use this if you have
        permission to submit to those companies (i.e. they're your own
        test postings).

    poetry run python scripts/demo.py --jobs 10 --applicant my_profile.json
        Custom number of jobs and a custom applicant payload.

PREREQUISITES:
    1. Server NOT running (this script drives the agent directly,
       no HTTP overhead).
    2. .env populated with GEMINI_API_KEY (or whatever provider you
       configure).
    3. Patchright Chromium installed:  poetry run patchright install chromium
    4. samples/demo_applicant.json exists and points to a real local PDF.

WHAT YOU SEE:
    - Chromium opens for each job (HEADLESS=false in this script)
    - The agent fills the form character-by-character at human speed
    - Per-job summary printed to the terminal
    - Final tracker xlsx written to logs/<batch_id>/tracker.xlsx
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

# Configure environment BEFORE importing jobpilot — we want the demo to be
# loud and visible regardless of what's in .env
os.environ.setdefault("HEADLESS", "false")
os.environ.setdefault("LOG_LEVEL", "info")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from jobpilot.api.schemas import Applicant, ApplyOptions
from jobpilot.flow.batch import run_batch


# Curated subset of the sample-list jobs from the brief.
# These are explicitly Greenhouse-hosted so the live adapter handles them.
DEMO_JOBS = [
    "https://job-boards.greenhouse.io/grammarly/jobs/7767680",
    "https://job-boards.greenhouse.io/geotab/jobs/5041684008",
    "https://job-boards.greenhouse.io/thumbtack/jobs/7746391",
    "https://job-boards.greenhouse.io/modernhealth/jobs/8465250002",
    "https://job-boards.greenhouse.io/marqeta/jobs/7724959",
    "https://job-boards.greenhouse.io/shift4/jobs/5092608007",
    "https://job-boards.greenhouse.io/wavelo/jobs/7683905003",
    "https://job-boards.greenhouse.io/rocketlawyer/jobs/5168904008",
    "https://job-boards.greenhouse.io/autotradercanada/jobs/7681994003",
    "https://job-boards.greenhouse.io/appdirectraas/jobs/8483919002",
]


async def main(args: argparse.Namespace) -> int:
    # Load applicant payload
    applicant_path = Path(args.applicant)
    if not applicant_path.exists():
        print(f"Applicant file not found: {applicant_path}")
        print("Create one based on samples/demo_applicant.json")
        return 2

    with applicant_path.open(encoding="utf-8") as f:
        applicant_data = json.load(f)

    applicant = Applicant(**applicant_data)

    # Pick jobs
    jobs = DEMO_JOBS[: args.jobs]

    # Configure options
    options = ApplyOptions(
        auto_submit=args.submit,
        headless=False,  # Watch live during demo
        llm_model=args.model,
        screenshot_on_failure=True,
    )

    # Print plan
    print()
    print("┌" + "─" * 72 + "┐")
    print("│  JobPilot — Demo Run".ljust(73) + "│")
    print("│  Brief compliance test against the sample list.".ljust(73) + "│")
    print("├" + "─" * 72 + "┤")
    print(f"│  Jobs to attempt:  {args.jobs}".ljust(73) + "│")
    print(f"│  Applicant:        {applicant.first_name} {applicant.last_name}".ljust(73) + "│")
    print(f"│  Resume PDF:       {applicant.resume_path[:50]}".ljust(73) + "│")
    print(f"│  LLM model:        {args.model} (Gemini)".ljust(73) + "│")
    print(f"│  Auto-submit:      {args.submit}".ljust(73) + "│")
    print(f"│  Pause between:    {args.pause}s".ljust(73) + "│")
    print("└" + "─" * 72 + "┘")
    print()

    # Run
    result = await run_batch(
        job_urls=jobs,
        applicant=applicant,
        options=options,
        pause_seconds=args.pause,
    )

    # Print results
    print()
    print("┌" + "─" * 72 + "┐")
    print("│  Results".ljust(73) + "│")
    print("├" + "─" * 72 + "┤")
    print(f"│  Batch:        {result.batch_id}".ljust(73) + "│")
    print(f"│  Total jobs:   {result.total_jobs}".ljust(73) + "│")
    print(f"│  Submitted:    {result.successes}".ljust(73) + "│")
    print(f"│  Blocked:      {result.blocked}".ljust(73) + "│")
    print(f"│  Failed:       {result.failures}".ljust(73) + "│")
    print(f"│  Tracker:      {result.tracker_path}".ljust(73) + "│")
    print("└" + "─" * 72 + "┘")
    print()

    print("Per-job:")
    for r in result.results:
        icon = "✓" if r.state in ("submitted", "pre_submit_ready") else \
               "🛑" if r.state == "blocked_by_bot_detection" else "✗"
        print(f"  {icon}  {r.company:<22} {r.state:<24} {r.duration_ms}ms  {r.run_id}")
        if r.reason:
            print(f"      └─ {r.reason}")

    print()
    print(f"Tracker xlsx generated at: {result.tracker_path}")
    print("Open it to see the spreadsheet that would be emailed to the applicant.")
    print()

    return 0 if result.successes > 0 else 1


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="JobPilot end-to-end demo.")
    p.add_argument("--jobs", type=int, default=5,
                   help="Number of jobs from the demo list to attempt (default: 5).")
    p.add_argument("--applicant", default="samples/demo_applicant.json",
                   help="Path to applicant JSON payload.")
    p.add_argument("--submit", action="store_true",
                   help="Actually submit applications. Off by default — "
                        "use this only against your own test postings.")
    p.add_argument("--model", default="gemini-2.0-flash",
                   help="Gemini model. Options: gemini-2.0-flash, gemini-2.5-flash, gemini-2.5-pro")
    p.add_argument("--pause", type=float, default=8.0,
                   help="Seconds to pause between jobs (default: 8.0).")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    sys.exit(asyncio.run(main(args)))
