"""Tests for the sensorimotor GridWorld experiment."""

from __future__ import annotations

import time

from solaris_ai_nn.experiments.sensorimotor_gridworld import run_sensorimotor_gridworld


def test_bounded_experiment_runs():
    start = time.perf_counter()
    result = run_sensorimotor_gridworld(steps=80, seed=7)
    assert time.perf_counter() - start < 60.0
    assert result.report["steps"] == 80


def test_report_contains_required_summaries():
    result = run_sensorimotor_gridworld(steps=80, seed=7)
    report = result.report
    for key in ("action_counts", "reactions", "energy", "substrate_metrics",
                "embodiment", "world_ascii", "telemetry"):
        assert key in report
    assert report["reactions"]["count"] >= 0
    assert "energy" in report["energy"] or "energy" in report
    assert report["embodiment"]["action_authority"] == "simulation-only"
    assert "A" in report["world_ascii"]


def test_persistence_paths_returned(tmp_path):
    result = run_sensorimotor_gridworld(steps=40, seed=3,
                                        state_dir=str(tmp_path / "sm"))
    assert "embodiment_state" in result.persistence_paths
    from pathlib import Path
    assert Path(result.persistence_paths["embodiment_state"]).exists()


def test_observe_only_and_substrate_flags():
    result = run_sensorimotor_gridworld(steps=40, seed=3, observe_only=True,
                                        substrate="spiking_recurrent")
    assert result.report["observe_only"] is True
    assert result.report["substrate"] == "spiking_recurrent"
    assert result.report["actions_executed"] == 0
