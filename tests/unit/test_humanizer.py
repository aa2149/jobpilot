# ============================================================================
# Copyright (c) 2026 Areej Ahmed. All rights reserved.
# Part of JobPilot — Submitted to the 1000Jobs Final Stage assessment.
# Licensed under the JobPilot Evaluation & Personal-Use License.
# See LICENSE and NOTICE.md in the repository root.
# ============================================================================
"""Statistical sanity check on the humanizer typing distribution.

We don't want a constant-rate keystream. The log-normal distribution should
produce variance and have no long runs of identical delays.
"""
from __future__ import annotations

import statistics

from jobpilot.humanizer.typing import _delay_ms


def test_delay_distribution_has_variance() -> None:
    samples = [_delay_ms() for _ in range(2000)]
    mean = statistics.mean(samples)
    stdev = statistics.stdev(samples)

    # Mean should be in the right neighborhood
    assert 80 < mean < 200, f"unexpected mean: {mean}"
    # Variance should be meaningful
    assert stdev > 20, f"distribution too tight, stdev: {stdev}"
    # And bounded
    assert min(samples) >= 35
    assert max(samples) <= 600


def test_no_long_runs_of_same_delay() -> None:
    samples = [_delay_ms() for _ in range(500)]
    # Round to 5ms buckets and check no bucket appears > 5 times in a row
    bucketed = [round(s / 5) * 5 for s in samples]
    longest_run = 1
    current = 1
    for i in range(1, len(bucketed)):
        if bucketed[i] == bucketed[i - 1]:
            current += 1
            longest_run = max(longest_run, current)
        else:
            current = 1
    assert longest_run < 6, f"suspicious run of identical delays: {longest_run}"
