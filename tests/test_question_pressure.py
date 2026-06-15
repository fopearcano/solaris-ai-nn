"""QuestionPressureEngine: missing/contradiction pressure; not verbal."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import InternalSign, SignKind
from solaris_ai_nn.sensorium_cognition import (
    QuestionPressureEngine,
    QuestionPressureType,
)


def test_missing_sign_creates_pressure():
    engine = QuestionPressureEngine()
    pressures = engine.generate(
        signs=[], failed_predictions=[], logos_tensions=[],
        anticipation_targets=["SIGN_X"], observed_targets=[])
    types = {p.pressure_type for p in pressures}
    assert QuestionPressureType.MISSING_EXPECTED_SIGN in types


def test_failed_prediction_creates_pressure():
    class _P:
        predicted_target = "SIGN_Y"
        prediction_id = "PRED_1"

    engine = QuestionPressureEngine()
    pressures = engine.generate(
        signs=[], failed_predictions=[_P()], logos_tensions=[],
        anticipation_targets=[], observed_targets=[])
    types = {p.pressure_type for p in pressures}
    assert QuestionPressureType.FAILED_PREDICTION in types


def test_ambiguity_and_contamination_create_pressure():
    sign = InternalSign(kind=SignKind.HUMAN_LABEL_CONTAMINATED,
                        modality_distribution={"human_textual": 3},
                        grounding_score=0.1)
    sign.ambiguity_score = 0.6
    engine = QuestionPressureEngine()
    pressures = engine.generate(
        signs=[sign], failed_predictions=[], logos_tensions=[],
        anticipation_targets=[], observed_targets=[])
    types = {p.pressure_type for p in pressures}
    assert QuestionPressureType.HIGH_CONTAMINATION in types
    assert QuestionPressureType.UNSTABLE_RELATION in types


def test_no_human_verbal_question_required():
    engine = QuestionPressureEngine()
    pressures = engine.generate(
        signs=[], failed_predictions=[], logos_tensions=[],
        anticipation_targets=["SIGN_X"], observed_targets=[])
    q = pressures[0]
    assert q.recommended_response in ("inspect", "compare", "wait", "simulate",
                                      "preserve_unknown")
    assert "not a human verbal question" in q.to_dict()["note"]
