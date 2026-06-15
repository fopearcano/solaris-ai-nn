"""PredictionEngine: prediction generated; failure stored; not understanding."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import InternalSign, SignKind
from solaris_ai_nn.semiogenesis.private_syntax import (
    PrivateSyntaxPattern,
    SyntaxRelation,
)
from solaris_ai_nn.sensorium_cognition import (
    PredictionEngine,
    PredictionOutcome,
    PredictionType,
)


def _setup():
    a = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="rf:01",
                     modality_distribution={"radio_frequency": 4})
    b = InternalSign(kind=SignKind.MODALITY_NATIVE, sign_code="vib:01",
                     modality_distribution={"vibration": 4})
    pat = PrivateSyntaxPattern(relation=SyntaxRelation.PREDICTS,
                              signs=[a.sign_id, b.sign_id], strength=0.7)
    return a, b, pat


def test_prediction_generated():
    a, b, pat = _setup()
    result = PredictionEngine().predict([a, b], [pat])
    assert result.predictions
    assert result.predictions[0].prediction_type == PredictionType.NEXT_SIGN
    assert result.predictions[0].predicted_target == b.sign_id


def test_failed_prediction_stored():
    a, b, pat = _setup()
    result = PredictionEngine().predict([a, b], [pat])
    # Resolve against observed targets that do NOT include the predicted sign.
    result.predictions[0].resolve(observed_targets=[a.sign_id])
    assert result.predictions[0].outcome == PredictionOutcome.FAILURE
    assert len(result.failed) == 1
    assert result.success_rate == 0.0


def test_successful_prediction_recorded():
    a, b, pat = _setup()
    result = PredictionEngine().predict([a, b], [pat])
    result.predictions[0].resolve(observed_targets=[b.sign_id])
    assert result.predictions[0].outcome == PredictionOutcome.SUCCESS
    assert result.success_rate == 1.0


def test_prediction_not_understanding_claim():
    a, b, pat = _setup()
    pred = PredictionEngine().predict([a, b], [pat]).predictions[0]
    assert "not proof of understanding" in pred.to_dict()["note"]


def test_metabolism_risk_predictions():
    a, b, pat = _setup()
    result = PredictionEngine().predict(
        [a, b], [pat], metabolism={"overload_state": True,
                                   "deprivation_state": True})
    types = {p.prediction_type for p in result.predictions}
    assert PredictionType.OVERLOAD_RISK in types
    assert PredictionType.DEPRIVATION_RISK in types
