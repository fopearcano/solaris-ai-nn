"""Tests for the SensorimotorSimulationRunner."""

from __future__ import annotations

import time

import pytest

from solaris_ai_nn.embodiment.simulation_runner import SensorimotorSimulationRunner


def test_bounded_runner_completes():
    start = time.perf_counter()
    runner = SensorimotorSimulationRunner(max_steps=80, seed=5)
    report = runner.run()
    assert time.perf_counter() - start < 30.0  # no infinite loop
    assert report["steps"] == 80
    assert report["telemetry"]["events"] > 0


def test_unbounded_requires_explicit_continuous():
    with pytest.raises(ValueError):
        SensorimotorSimulationRunner()
    runner = SensorimotorSimulationRunner(continuous=True, max_steps=None)
    assert runner.continuous is True  # constructible; never run in tests


def test_observe_only_mode_executes_nothing():
    runner = SensorimotorSimulationRunner(max_steps=60, seed=5,
                                          execute_suggestions=False)
    report = runner.run()
    assert report["observe_only"] is True
    assert report["actions_executed"] == 0
    assert report["action_counts"] == {}
    # But perception still drove the substrate.
    assert report["telemetry"]["reservoir_updates"] > 0


def test_execute_mode_produces_action_results():
    runner = SensorimotorSimulationRunner(max_steps=60, seed=5)
    report = runner.run()
    assert report["actions_executed"] > 0
    assert sum(report["action_counts"].values()) > 0
    assert len(runner.action_history) > 0
    # All executed actions were inside the declared space.
    from solaris_ai_nn.embodiment.action_space import ALLOWED_ACTIONS
    assert set(report["action_counts"]) <= set(ALLOWED_ACTIONS)


def test_duration_bound_works():
    runner = SensorimotorSimulationRunner(max_duration_s=0.2, seed=5)
    start = time.perf_counter()
    runner.run()
    assert time.perf_counter() - start < 10.0


def test_persistence_files_written(tmp_path):
    runner = SensorimotorSimulationRunner(max_steps=40, seed=5,
                                          state_dir=str(tmp_path / "emb"))
    runner.run()
    assert (tmp_path / "emb" / "embodiment_state.json").exists()
    assert (tmp_path / "emb" / "body_state.json").exists()
    assert (tmp_path / "emb" / "world_state.json").exists()
