"""Tests for the restart recovery demo (state restore + simulated crash)."""

from __future__ import annotations

from solaris_ai_nn.experiments.restart_recovery import run_restart_demo
from solaris_ai_nn.runtime.persistence import (
    BRAIN_DEATH_GAP,
    UNEXPECTED_DEATH,
    ContinuityLog,
)


def test_simulated_restart_restores_state(tmp_path):
    result = run_restart_demo(state_dir=str(tmp_path / "brain"), steps=50, seed=7)
    # Two sessions ran; lifetime accumulates across the restart.
    assert result.restart_count == 1
    assert result.lifetime_steps == result.session1_steps + result.session2_steps
    # State was genuinely restored: nonzero reservoir norm and learned habits.
    assert result.restored_reservoir_norm > 0.0
    assert result.restored_habit_count > 0


def test_clean_restart_has_no_unexpected_death(tmp_path):
    result = run_restart_demo(state_dir=str(tmp_path / "brain"), steps=40, seed=7)
    assert result.unexpected_death_detected is False


def test_simulated_crash_logs_unexpected_death(tmp_path):
    state_dir = tmp_path / "brain"
    result = run_restart_demo(
        state_dir=str(state_dir), steps=40, seed=7, simulate_crash=True
    )
    assert result.unexpected_death_detected is True
    assert result.brain_death_gap_seconds >= 4.0

    # The continuity log on disk contains both crash-detection events.
    log = ContinuityLog(result.continuity_log_path)
    types = [r["event_type"] for r in log.read_all()]
    assert UNEXPECTED_DEATH in types
    assert BRAIN_DEATH_GAP in types


def test_crash_simulation_does_not_kill_process(tmp_path):
    # The function must return normally (no process kill) even with a crash sim.
    result = run_restart_demo(
        state_dir=str(tmp_path / "brain"), steps=30, seed=3, simulate_crash=True
    )
    assert result.lifetime_steps > 0  # we got here => process survived
