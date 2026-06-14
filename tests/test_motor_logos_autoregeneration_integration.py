"""Motor <-> LOGOS / AutoRegeneration.

A blocked action intention (the desire to act vs the prohibition on acting) is
a preserved tension for LOGOS, not something to resolve by acting; sandbox
corruption / ledger write failure are degradation signals for AutoRegeneration
-- and neither subsystem can grant real-world action.
"""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    ActionVetoLayer,
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
    VetoReason,
)


def test_real_world_veto_becomes_tension():
    layer = ActionVetoLayer()
    veto = layer.evaluate(MotorAction(MotorActionType.MOVE_EAST,
                                      scope=MotorActionScope.FORBIDDEN_REAL_WORLD))
    assert veto.becomes_tension is True
    assert veto.reason == VetoReason.REAL_WORLD_ACTION_FORBIDDEN


def test_unknown_scope_veto_becomes_hypothesis_seed():
    layer = ActionVetoLayer()
    a = MotorAction(MotorActionType.MOVE_EAST)
    object.__setattr__(a, "scope", "weird_scope")  # not runnable
    veto = layer.evaluate(a)
    assert veto is not None
    assert veto.becomes_hypothesis_seed is True


def test_sandbox_health_signals_degradation(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path))
    rt.initialize()
    assert rt.sandbox_health() == "ok"
    # Simulate a ledger persistence failure -> degraded health for AutoRegen.
    rt.ledger.write_failures = 1
    assert rt.sandbox_health() == "degraded"


def test_emergency_stop_only_allows_safe_actions(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path))
    rt.initialize()
    rt.request_emergency_stop()
    assert rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                                 scope=MotorActionScope.SANDBOX_ONLY)
                     )["executed"] is False
    assert rt.submit(MotorAction(MotorActionType.REST,
                                 scope=MotorActionScope.INTERNAL_ONLY)
                     )["executed"] is True
