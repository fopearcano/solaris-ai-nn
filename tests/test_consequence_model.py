"""ConsequenceModel: predicts then records simulated action outcomes."""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    ActuatorResult,
    ConsequenceModel,
    MotorAction,
    MotorActionType,
)


def _result(action_id, state_changed, valence):
    return ActuatorResult(action_id, MotorActionType.MOVE_EAST,
                          reaction_valence=valence, state_changed=state_changed)


def test_predict_then_record_correct():
    cm = ConsequenceModel()
    a = MotorAction(MotorActionType.MOVE_EAST)
    cm.predict(a)  # move -> expects state change
    rec = cm.record(a.action_id, _result(a.action_id, True, 0.0))
    assert rec.prediction_correct is True
    assert cm.prediction_accuracy() == 1.0


def test_misprediction_seeds_hypothesis():
    cm = ConsequenceModel()
    a = MotorAction(MotorActionType.MOVE_EAST)
    cm.predict(a)
    cm.record(a.action_id, _result(a.action_id, False, 0.0))  # no change
    assert cm.prediction_accuracy() == 0.0
    seeds = cm.hypothesis_seeds()
    assert seeds and a.action_id in seeds[0]


def test_records_are_simulated():
    cm = ConsequenceModel()
    a = MotorAction(MotorActionType.LOOK)
    cm.predict(a)
    rec = cm.record(a.action_id, _result(a.action_id, False, 0.0))
    assert rec.simulated is True


def test_accuracy_empty_is_zero():
    assert ConsequenceModel().prediction_accuracy() == 0.0


def test_snapshot_reports_counts():
    cm = ConsequenceModel()
    a = MotorAction(MotorActionType.MOVE_EAST)
    cm.predict(a)
    cm.record(a.action_id, _result(a.action_id, True, 0.0))
    snap = cm.snapshot()
    assert snap["record_count"] == 1
