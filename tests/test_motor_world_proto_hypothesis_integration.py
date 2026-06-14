"""Motor <-> World model / Proto-language / Hypothesis.

Simulated action consequences are predicted then compared to observation;
mispredictions become hypothesis seeds (simulation-scoped), and repeated
simulated outcomes are the raw material for world-model / proto-symbol grounding
-- all simulation-only, never real-world evidence.
"""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    ActuatorResult,
    ConsequenceModel,
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)


def test_misprediction_becomes_hypothesis_seed():
    cm = ConsequenceModel()
    a = MotorAction(MotorActionType.MOVE_EAST)
    cm.predict(a)  # move -> expects state change
    cm.record(a.action_id,
              ActuatorResult(a.action_id, MotorActionType.MOVE_EAST,
                             state_changed=False))  # observed: no change
    seeds = cm.hypothesis_seeds()
    assert seeds and seeds[0].startswith("action_consequence::")


def test_simulated_run_accumulates_consequence_records(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path), seed=2)
    rt.initialize()
    for _ in range(4):
        rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                              scope=MotorActionScope.SANDBOX_ONLY))
    snap = rt.snapshot()
    assert snap["consequence"]["record_count"] >= 1


def test_prediction_accuracy_is_simulation_scoped(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path), seed=2)
    rt.initialize()
    rt.submit(MotorAction(MotorActionType.REST,
                          scope=MotorActionScope.SANDBOX_ONLY))
    acc = rt.summary()["prediction_accuracy"]
    assert 0.0 <= acc <= 1.0


def test_consequence_records_are_simulated():
    cm = ConsequenceModel()
    a = MotorAction(MotorActionType.LOOK)
    cm.predict(a)
    rec = cm.record(a.action_id,
                    ActuatorResult(a.action_id, MotorActionType.LOOK))
    assert rec.simulated is True
