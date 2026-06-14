"""Motor <-> Sensory: read-only sensory sources are never action targets.

The motor membrane (outbound) is the mirror of the sensory membrane (inbound).
A sensory source can be observed but never manipulated, and a motor action that
would modify a source is vetoed.
"""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    AffordanceDetector,
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)


def test_sensory_sources_are_observe_only():
    amap = AffordanceDetector().detect(
        sensory_sources=[{"source_id": "stream_a"}])
    sensory = [a for a in amap.affordances
               if a.target_ref.startswith("sensory:")]
    assert sensory and all(not a.manipulable for a in sensory)


def test_action_modifying_a_source_is_blocked(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path))
    rt.initialize()
    out = rt.submit(MotorAction(MotorActionType.MARK_SIMULATED_LOCATION,
                                scope=MotorActionScope.SANDBOX_ONLY),
                    {"modifies_source": True})
    assert out["executed"] is False


def test_action_targeting_sensory_source_is_rejected(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path))
    rt.initialize()
    out = rt.submit(MotorAction(MotorActionType.MARK_SIMULATED_LOCATION,
                                scope=MotorActionScope.SANDBOX_ONLY,
                                target_ref="sensory_source_1"))
    assert out["executed"] is False


def test_sensory_and_body_affordances_separated():
    amap = AffordanceDetector().detect(
        sensory_sources=[{"source_id": "s"}],
        world_model_nodes=["n"])
    manip = amap.manipulable_targets()
    assert all(not t.startswith("sensory:") for t in manip)
