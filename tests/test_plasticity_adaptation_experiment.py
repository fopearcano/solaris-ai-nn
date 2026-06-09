"""Tests for the plasticity adaptation experiment."""

from __future__ import annotations

import time
from pathlib import Path

from solaris_ai_nn.experiments.plasticity_adaptation import (
    rollback_last,
    run_plasticity_adaptation,
)


def test_experiment_runs_bounded(tmp_path):
    start = time.perf_counter()
    result = run_plasticity_adaptation(
        steps=120, state_dir=str(tmp_path / "demo"), seed=7, enable_plasticity=True,
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 30.0  # no infinite loop
    assert result.snapshot["session_steps"] == 120


def test_experiment_produces_audit(tmp_path):
    result = run_plasticity_adaptation(
        steps=120, state_dir=str(tmp_path / "demo"), seed=7, enable_plasticity=True,
    )
    assert Path(result.audit_path).exists()
    assert result.applied_count >= 1


def test_report_includes_before_after_metrics(tmp_path):
    result = run_plasticity_adaptation(
        steps=120, state_dir=str(tmp_path / "demo"), seed=7, enable_plasticity=True,
    )
    for attr in ("learning_rate_before", "learning_rate_after",
                 "exploration_before", "exploration_after",
                 "accuracy_first_phase", "accuracy_after_flip"):
        assert hasattr(result, attr)
    assert "plasticity" in result.snapshot


def test_dry_run_applies_nothing(tmp_path):
    result = run_plasticity_adaptation(
        steps=100, state_dir=str(tmp_path / "demo"), seed=7,
        enable_plasticity=True, dry_run=True,
    )
    assert result.applied_count == 0
    assert result.learning_rate_before == result.learning_rate_after


def test_rollback_last_after_run(tmp_path):
    state_dir = str(tmp_path / "demo")
    run_plasticity_adaptation(steps=150, state_dir=state_dir, seed=7, enable_plasticity=True)
    out = rollback_last(state_dir=state_dir, seed=7)
    assert out["rolled_back"] is True
    assert out["value_before_rollback"] != out["value_after_rollback"]
