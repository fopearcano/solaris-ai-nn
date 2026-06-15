"""AnticipationEngine: expected sign/absence tracked; feeds probe."""

from __future__ import annotations

from solaris_ai_nn.sensorium_cognition import (
    AnticipationEngine,
    AnticipationKind,
    PredictionType,
    SensoriumPrediction,
)


def test_expected_sign_tracked():
    pred = SensoriumPrediction(prediction_type=PredictionType.NEXT_SIGN,
                               predicted_target="SIGN_B", confidence=0.6)
    state = AnticipationEngine().update([pred])
    assert "SIGN_B" in state.expected_targets()
    assert state.events[0].kind == AnticipationKind.EXPECTED_SIGN


def test_expected_absence_tracked():
    pred = SensoriumPrediction(prediction_type=PredictionType.MISSING_SIGN,
                               predicted_target="SIGN_C", confidence=0.4)
    state = AnticipationEngine().update([pred])
    assert state.events[0].kind == AnticipationKind.EXPECTED_ABSENCE


def test_anticipation_feeds_probe():
    engine = AnticipationEngine()
    engine.update([SensoriumPrediction(
        prediction_type=PredictionType.NEXT_SIGN, predicted_target="SIGN_X")])
    payload = engine.probe_payload()
    assert "SIGN_X" in payload["expected_targets"]
    assert "probe" in payload["note"]


def test_anticipation_not_subjective():
    state = AnticipationEngine().update([SensoriumPrediction(
        prediction_type=PredictionType.NEXT_SIGN, predicted_target="S")])
    assert "not imagination or subjective experience" in \
        state.events[0].to_dict()["note"]
