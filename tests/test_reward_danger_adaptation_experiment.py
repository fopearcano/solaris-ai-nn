"""Tests for the reward/danger adaptation experiment."""

from __future__ import annotations

import time

from solaris_ai_nn.experiments.reward_danger_adaptation import (
    run_reward_danger_adaptation,
)


def test_bounded_experiment_runs_and_records_feedback():
    start = time.perf_counter()
    result = run_reward_danger_adaptation(steps=150, seed=7)
    assert time.perf_counter() - start < 60.0  # no infinite loop
    assert result.steps == 150
    assert result.reactions_recorded > 0


def test_tendency_verdict_is_explicit_either_way():
    result = run_reward_danger_adaptation(steps=150, seed=7)
    # Changed or not, the verdict must say so clearly.
    if result.tendencies_changed:
        assert "shifted" in result.verdict
    else:
        assert "no clear tendency change" in result.verdict
    d = result.to_dict()
    for key in ("early_mean_valence", "late_mean_valence",
                "early_reward_events", "late_reward_events",
                "early_danger_events", "late_danger_events",
                "tendencies_changed", "verdict"):
        assert key in d


def test_adaptation_observed_on_reference_seed():
    """On the reference seed the tendencies measurably improve."""
    result = run_reward_danger_adaptation(steps=200, seed=7)
    assert result.tendencies_changed is True
    assert result.late_mean_valence > result.early_mean_valence
