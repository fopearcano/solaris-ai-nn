"""Tests for the ContinuousRunner."""

from __future__ import annotations

import time

import pytest

from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.signals import canonical as C


def test_refuses_unbounded_run_unless_continuous(tmp_path):
    with pytest.raises(ValueError):
        ContinuousRunner(state_dir=tmp_path / "s", max_steps=None, max_duration_s=None)
    # Explicit continuous=True is allowed at construction (we do not run it).
    runner = ContinuousRunner(state_dir=tmp_path / "s2", continuous=True)
    assert runner.continuous is True


def test_bounded_runner_completes_by_steps(tmp_path):
    runner = ContinuousRunner(
        state_dir=tmp_path / "s", max_steps=60, checkpoint_interval_steps=20,
        heartbeat_interval_s=0.0,
    )
    snap = runner.run()
    assert snap["session_steps"] == 60
    assert snap["lifecycle"]["state"] == "dead"
    assert snap["lifecycle"]["graceful"] is True


def test_bounded_runner_completes_by_duration(tmp_path):
    start = time.perf_counter()
    runner = ContinuousRunner(
        state_dir=tmp_path / "s", max_steps=None, max_duration_s=0.2,
        checkpoint_interval_steps=1000,
    )
    runner.run()
    assert time.perf_counter() - start < 10.0  # bounded, no infinite loop


def test_checkpoint_is_created(tmp_path):
    runner = ContinuousRunner(
        state_dir=tmp_path / "s", max_steps=50, checkpoint_interval_steps=20,
    )
    runner.run()
    assert runner.pm.checkpoint_path.exists()
    assert runner.pm.manifest_path.exists()
    # interval checkpoints at 20, 40, plus a final one => >= 3.
    assert runner.telemetry.checkpoints >= 3


def test_snapshot_returns_expected_fields(tmp_path):
    runner = ContinuousRunner(state_dir=tmp_path / "s", max_steps=30)
    snap = runner.run()
    for key in (
        "run_id", "session_id", "state_dir", "continuity_log_path", "lifecycle",
        "session_steps", "lifetime_steps", "restart_count", "checkpoints",
        "reservoir_norm", "habit_pathways", "telemetry",
    ):
        assert key in snap


def test_stop_requests_graceful_halt(tmp_path):
    runner = ContinuousRunner(state_dir=tmp_path / "s", max_steps=1000)

    def stimulus_provider(step):
        if step >= 10:
            runner.stop("seen enough")
        return C.Stimulus(payload="x", intensity=0.5)

    runner.stimulus_provider = stimulus_provider
    snap = runner.run()
    assert snap["session_steps"] <= 12  # stopped soon after step 10
    assert snap["lifecycle"]["graceful"] is True
