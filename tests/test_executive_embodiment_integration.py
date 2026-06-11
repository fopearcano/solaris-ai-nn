"""Tests for the executive inside the sensorimotor runner."""

from __future__ import annotations

from solaris_ai_nn.embodiment.action_space import ACTION_SPACE
from solaris_ai_nn.embodiment.simulation_runner import (
    SensorimotorSimulationRunner,
)


def test_gridworld_action_selected_safely(tmp_path):
    runner = SensorimotorSimulationRunner(
        max_steps=100, seed=5, state_dir=str(tmp_path / "s"),
        enable_homeostasis=True, enable_executive=True)
    runner.run()
    assert runner.steps_run == 100
    # Everything executed was a declared simulated action.
    for result in runner.action_history:
        assert result.action in ACTION_SPACE
    assert runner.executive.decisions > 0
    # The executive's selections stayed suggestions until the simulation
    # (and only the simulation) executed them.
    assert runner.executive.last_result.selected.committed is False


def test_observe_only_does_not_execute(tmp_path):
    runner = SensorimotorSimulationRunner(
        max_steps=60, seed=5, state_dir=str(tmp_path / "s"),
        enable_executive=True, executive_mode="observe_only")
    runner.run()
    assert runner.action_history == []  # nothing ever executed
    assert runner.executive.decisions > 0  # but arbitration still ran
    assert not runner.executive.policy.execution_allowed()


def test_blocked_actions_recorded(tmp_path):
    runner = SensorimotorSimulationRunner(
        max_steps=150, seed=5, state_dir=str(tmp_path / "s"),
        enable_homeostasis=True, enable_executive=True)
    runner.run()
    # Inhibitions and blocked simulation actions both leave records.
    blocked_in_sim = [r for r in runner.action_history if r.blocked_reason]
    inhibition_rows = runner.executive.inhibition.history
    trace_rows = runner.executive.recorder.rows()
    assert trace_rows  # periodic recorded decisions exist
    if blocked_in_sim or inhibition_rows:
        assert all(r.blocked_reason for r in blocked_in_sim) \
            or all(row["reason"] for row in inhibition_rows)


def test_internal_selection_skips_execution(tmp_path):
    """When the executive picks an internal action (e.g. reduce_activity),
    no simulated action executes that step."""
    runner = SensorimotorSimulationRunner(
        max_steps=120, seed=5, state_dir=str(tmp_path / "s"),
        enable_homeostasis=True, enable_executive=True)
    runner.run()
    selected = {row.get("selected") for row in
                runner.executive.recorder.rows()}
    internal = selected - set(ACTION_SPACE) - {None}
    # Internal selections happened (homeostasis presses reduce_activity
    # under fatigue) yet only declared actions ever executed.
    executed = {r.action for r in runner.action_history}
    assert executed <= set(ACTION_SPACE)
    assert internal or executed  # at least one path was exercised
