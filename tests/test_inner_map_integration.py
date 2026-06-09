"""Tests for Inner MAP integration with the ContinuousRunner."""

from __future__ import annotations

from solaris_ai_nn.inner_map.serialization import load_inner_map
from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner


def test_runner_updates_inner_map(tmp_path):
    runner = ContinuousRunner(
        state_dir=tmp_path / "brain", max_steps=60, checkpoint_interval_steps=20,
        inner_map_update_interval_steps=10, heartbeat_interval_s=0.0,
    )
    snap = runner.run()
    assert runner.observer is not None
    assert "inner_map" in snap
    assert "boundaries" in snap
    assert "memory" in snap
    assert snap["inner_map"]["continuity"]["session_steps"] == 60


def test_checkpoint_saves_inner_map_json(tmp_path):
    runner = ContinuousRunner(
        state_dir=tmp_path / "brain", max_steps=40, checkpoint_interval_steps=20,
    )
    runner.run()
    assert runner.pm.inner_map_path.exists()
    model = load_inner_map(runner.pm.inner_map_path)
    assert model.continuity.session_steps > 0
    assert model.neural.reservoir_size == runner.bridge.esn.n_reservoir


def test_loaded_inner_map_contains_restored_continuity(tmp_path):
    state_dir = tmp_path / "brain"
    # Session 1.
    ContinuousRunner(state_dir=state_dir, max_steps=50, checkpoint_interval_steps=25).run()
    # Session 2 (restart from the same state dir).
    runner2 = ContinuousRunner(state_dir=state_dir, max_steps=50, checkpoint_interval_steps=25)
    runner2.run()

    model = load_inner_map(runner2.pm.inner_map_path)
    assert model.continuity.restart_count == 1
    assert model.continuity.lifetime_steps == 100  # 50 + 50
    assert model.run_id == runner2.run_id


def test_inner_map_can_be_disabled(tmp_path):
    runner = ContinuousRunner(state_dir=tmp_path / "brain", max_steps=20, inner_map=False)
    snap = runner.run()
    assert runner.observer is None
    assert "inner_map" not in snap
    assert not runner.pm.inner_map_path.exists()
