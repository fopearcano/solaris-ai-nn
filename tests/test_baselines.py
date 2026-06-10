"""Tests for the baselines."""

from __future__ import annotations

import time

from solaris_ai_nn.evaluation.baselines import (
    fixed_action_baseline,
    no_habit_baseline,
    no_plasticity_baseline,
    observe_only_baseline,
    random_action_baseline,
)


def test_random_baseline_runs_bounded():
    start = time.perf_counter()
    out = random_action_baseline(steps=100, seed=7)
    assert time.perf_counter() - start < 10.0
    assert out["bounded"] is True
    assert 0.0 <= out["late_accuracy"] <= 1.0
    # Deterministic per seed.
    assert out == random_action_baseline(steps=100, seed=7)


def test_fixed_baseline_is_one_third_ish():
    out = fixed_action_baseline(steps=99, seed=7)
    assert abs(out["accuracy"] - 1 / 3) < 0.05


def test_no_plasticity_baseline_disables_plasticity_but_learns():
    out = no_plasticity_baseline(steps=120, seed=7)
    assert out["plasticity_enabled"] is False
    # Online learning alone beats the random floor on this world.
    assert out["late_accuracy"] > random_action_baseline(120, 7)["late_accuracy"]


def test_ablation_baselines_flagged():
    assert no_habit_baseline(steps=60, seed=7)["habit_disabled"] is True
    out = observe_only_baseline(steps=60, seed=7)
    assert out["feedback_disabled"] is True
