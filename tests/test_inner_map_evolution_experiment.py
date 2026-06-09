"""Tests for the Inner MAP evolution experiment."""

from __future__ import annotations

import time

from solaris_ai_nn.experiments.inner_map_evolution import run_inner_map_evolution


def test_experiment_runs_bounded(tmp_path):
    start = time.perf_counter()
    result = run_inner_map_evolution(
        steps=80, state_dir=str(tmp_path / "demo"), seed=7,
        checkpoint_interval=40, inner_map_update_interval=10, prune_interval=40,
    )
    elapsed = time.perf_counter() - start
    assert elapsed < 30.0  # no infinite loop
    assert result.snapshot["session_steps"] == 80


def test_report_contains_expected_keys(tmp_path):
    result = run_inner_map_evolution(steps=60, state_dir=str(tmp_path / "demo"), seed=3)
    # Result fields.
    for attr in ("reservoir_norm", "strongest_habits", "pruning_count",
                 "dominant_signal_type", "suggested_action", "hard_boundaries",
                 "mermaid_preview", "inner_map_path"):
        assert hasattr(result, attr)
    # Snapshot sections required by the spec.
    for key in ("telemetry", "lifecycle", "bridge", "memory", "inner_map", "boundaries"):
        assert key in result.snapshot
    assert "action_authority_suggest_only" in result.hard_boundaries
    assert result.mermaid_preview.startswith("flowchart LR")


def test_inner_map_file_written(tmp_path):
    result = run_inner_map_evolution(steps=60, state_dir=str(tmp_path / "demo"), seed=3)
    from pathlib import Path

    assert Path(result.inner_map_path).exists()


def test_pruning_runs_when_interval_reached(tmp_path):
    result = run_inner_map_evolution(
        steps=120, state_dir=str(tmp_path / "demo"), seed=7, prune_interval=40,
    )
    # prune at 40, 80, 120 => at least 2 recorded.
    assert result.pruning_count >= 2
