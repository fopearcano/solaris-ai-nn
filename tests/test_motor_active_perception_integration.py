"""Motor <-> Active Perception: action candidates become bounded intentions.

Active perception proposes where to look / what to do; those candidates become
MotorActions that still pass the full gated pipeline. Curiosity never overrides
the firewall, and look/inspect actions stay observation-scoped.
"""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)


def _runtime(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path), seed=2)
    rt.initialize()
    return rt


def test_look_action_is_information_seeking(tmp_path):
    rt = _runtime(tmp_path)
    out = rt.submit(MotorAction(MotorActionType.LOOK,
                                scope=MotorActionScope.SANDBOX_ONLY))
    assert out["executed"] is True


def test_inspect_boundary_runs_in_sandbox(tmp_path):
    rt = _runtime(tmp_path)
    out = rt.submit(MotorAction(MotorActionType.INSPECT_BOUNDARY,
                                scope=MotorActionScope.SANDBOX_ONLY))
    assert out["executed"] is True


def test_curiosity_cannot_override_firewall(tmp_path):
    rt = _runtime(tmp_path)
    # A high-information-gain action that is real-world scoped is still blocked.
    a = MotorAction(MotorActionType.MOVE_EAST,
                    scope=MotorActionScope.FORBIDDEN_REAL_WORLD,
                    expected_information_gain=10.0)
    out = rt.submit(a)
    assert out["executed"] is False


def test_information_gain_recorded_for_simulated_action(tmp_path):
    rt = _runtime(tmp_path)
    out = rt.submit(MotorAction(MotorActionType.LOOK,
                                scope=MotorActionScope.SANDBOX_ONLY))
    assert "result" in out
    assert "information_gain" in out["result"]
