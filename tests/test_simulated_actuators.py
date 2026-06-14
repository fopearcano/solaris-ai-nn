"""Simulated actuators: gridworld body and internal-only requests."""

from __future__ import annotations

from solaris_ai_nn.embodiment.grid_world import GridWorld
from solaris_ai_nn.motor_membrane import (
    GridWorldActuator,
    InternalActuator,
    MotorAction,
    MotorActionType,
)


def test_gridworld_actuator_handles_gridworld_actions():
    act = GridWorldActuator(GridWorld(seed=3))
    assert act.can_handle(MotorAction(MotorActionType.MOVE_EAST))
    assert not act.can_handle(MotorAction(MotorActionType.REQUEST_REPLAY))


def test_gridworld_move_returns_simulated_result():
    act = GridWorldActuator(GridWorld(seed=3))
    r = act.execute(MotorAction(MotorActionType.MOVE_EAST))
    assert r.simulated is True
    assert r.action_type == MotorActionType.MOVE_EAST


def test_gridworld_mark_records_location():
    act = GridWorldActuator(GridWorld(seed=3))
    r = act.execute(MotorAction(MotorActionType.MARK_SIMULATED_LOCATION))
    assert r.state_changed is True
    assert "marked" in r.effect_summary


def test_gridworld_look_is_observation():
    act = GridWorldActuator(GridWorld(seed=3))
    r = act.execute(MotorAction(MotorActionType.LOOK))
    assert r.simulated is True


def test_internal_actuator_handles_internal_requests():
    act = InternalActuator()
    assert act.can_handle(MotorAction(MotorActionType.REQUEST_CONSOLIDATION))
    assert not act.can_handle(MotorAction(MotorActionType.MOVE_EAST))


def test_internal_actuator_emits_request_only():
    act = InternalActuator()
    r = act.execute(MotorAction(MotorActionType.REQUEST_REPLAY))
    assert r.state_changed is False
    assert "internal_request:latent_replay" in r.effect_summary
    assert r.simulated is True


def test_all_actuator_results_are_simulated():
    gw = GridWorldActuator(GridWorld(seed=1))
    for kind in (MotorActionType.MOVE_NORTH, MotorActionType.REST,
                 MotorActionType.INSPECT_BOUNDARY):
        assert gw.execute(MotorAction(kind)).simulated is True
