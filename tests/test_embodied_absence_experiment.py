"""Tests for the embodied absence experiment."""

from __future__ import annotations

import time

from solaris_ai_nn.experiments.embodied_absence import run_embodied_absence


def test_bounded_and_absence_stimuli_occur():
    start = time.perf_counter()
    result = run_embodied_absence(steps=100, seed=7)
    assert time.perf_counter() - start < 60.0  # no infinite loop
    assert result.steps == 100
    assert result.absence_stimuli > 0
    assert result.absence_ratio > 0.0


def test_substrate_updates_during_low_stimulus_windows():
    result = run_embodied_absence(steps=100, seed=7)
    assert result.substrate_updates > 0
    assert result.went_inert is False


def test_feedback_classified():
    result = run_embodied_absence(steps=100, seed=7)
    # Both counters exist (values may legitimately be zero on some seeds).
    assert result.useful_actions >= 0
    assert result.useless_actions >= 0
    assert result.to_dict()["absence_stimuli"] == result.absence_stimuli
