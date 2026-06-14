"""MotorAction invariants: never real-world authority, scope is sanitized."""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    MotorAction,
    MotorActionResult,
    MotorActionScope,
    MotorActionStatus,
    MotorActionType,
)


def test_action_never_has_real_world_authority():
    a = MotorAction(MotorActionType.MOVE_EAST,
                    real_world_authority=True, simulated_only=False)
    assert a.real_world_authority is False
    assert a.simulated_only is True


def test_unknown_action_type_becomes_no_action():
    a = MotorAction("launch_missiles")
    assert a.action_type == MotorActionType.NO_ACTION


def test_unknown_scope_becomes_forbidden_real_world():
    a = MotorAction(MotorActionType.LOOK, scope="touch_grass")
    assert a.scope == MotorActionScope.FORBIDDEN_REAL_WORLD
    assert a.is_real_world_scope is True
    assert a.is_runnable_scope is False


def test_runnable_scopes_exclude_forbidden_real_world():
    assert MotorActionScope.FORBIDDEN_REAL_WORLD not in MotorActionScope.RUNNABLE
    for scope in MotorActionScope.RUNNABLE:
        assert MotorAction(MotorActionType.REST, scope=scope).is_runnable_scope


def test_blocked_status_set_is_consistent():
    assert MotorActionStatus.VETOED in MotorActionStatus.BLOCKED
    assert MotorActionStatus.BLOCKED_BY_FIREWALL in MotorActionStatus.BLOCKED
    assert MotorActionStatus.EXECUTED_IN_SIMULATION not in \
        MotorActionStatus.BLOCKED


def test_roundtrip_to_from_dict():
    a = MotorAction(MotorActionType.LOOK, scope=MotorActionScope.SANDBOX_ONLY)
    b = MotorAction.from_dict(a.to_dict())
    assert b.action_type == a.action_type and b.scope == a.scope
    assert b.real_world_authority is False


def test_result_defaults_simulated():
    r = MotorActionResult(action_id="x", action_type=MotorActionType.REST,
                          status=MotorActionStatus.EXECUTED_IN_SIMULATION)
    assert r.simulated is True and r.real_world_authority is False
