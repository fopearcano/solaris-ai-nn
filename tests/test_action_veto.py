"""ActionVetoLayer: refuses forbidden actions; real-world vetoes are final."""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    ActionVetoLayer,
    MotorAction,
    MotorActionScope,
    MotorActionStatus,
    MotorActionType,
    VetoReason,
)


def _action(scope=MotorActionScope.SANDBOX_ONLY,
            kind=MotorActionType.MOVE_EAST):
    return MotorAction(kind, scope=scope)


def test_real_world_action_is_vetoed_finally():
    layer = ActionVetoLayer()
    veto = layer.evaluate(_action(scope=MotorActionScope.FORBIDDEN_REAL_WORLD))
    assert veto is not None
    assert veto.reason == VetoReason.REAL_WORLD_ACTION_FORBIDDEN
    assert veto.final is True


def test_source_modification_is_vetoed_finally():
    layer = ActionVetoLayer()
    veto = layer.evaluate(_action(), {"modifies_source": True})
    assert veto.reason == VetoReason.SOURCE_MODIFICATION_FORBIDDEN
    assert veto.final is True


def test_missing_executive_is_vetoed():
    layer = ActionVetoLayer()
    veto = layer.evaluate(_action(), {"executive_validated": False})
    assert veto.reason == VetoReason.MISSING_EXECUTIVE_APPROVAL
    assert veto.final is False


def test_emergency_mode_allows_only_safe_actions():
    layer = ActionVetoLayer()
    assert layer.evaluate(_action(), {"emergency_mode": True}) is not None
    assert layer.evaluate(_action(kind=MotorActionType.REST),
                          {"emergency_mode": True}) is None


def test_safe_sandbox_action_is_not_vetoed():
    layer = ActionVetoLayer()
    assert layer.evaluate(_action()) is None


def test_veto_sets_status_and_counts():
    layer = ActionVetoLayer()
    a = _action(scope=MotorActionScope.FORBIDDEN_REAL_WORLD)
    layer.evaluate(a)
    assert a.status == MotorActionStatus.VETOED
    assert layer.veto_count() == 1
    assert layer.snapshot()["final_count"] == 1


def test_final_reasons_set():
    assert VetoReason.REAL_WORLD_ACTION_FORBIDDEN in VetoReason.FINAL
    assert VetoReason.SOURCE_MODIFICATION_FORBIDDEN in VetoReason.FINAL
    assert VetoReason.MISSING_EXECUTIVE_APPROVAL not in VetoReason.FINAL
