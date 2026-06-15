"""SignUtilityEvaluator: compression/prediction utility; useless demoted."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import (
    InternalSign,
    SignKind,
    SignStatus,
    SignUtilityEvaluator,
)


def test_compression_utility_computed():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 4},
                     compression_utility=0.7, recurrence_count=4)
    res = SignUtilityEvaluator().evaluate(s)
    assert res.compression_utility == 0.7
    assert res.overall >= 0.0


def test_prediction_utility_computed():
    s = InternalSign(kind=SignKind.RHYTHM,
                     modality_distribution={"vibration": 4},
                     prediction_utility=0.8, recurrence_count=4)
    res = SignUtilityEvaluator().evaluate(s)
    assert res.prediction_utility == 0.8
    assert "not therefore true" in res.to_dict()["note"]


def test_useless_sign_demoted_from_stable():
    s = InternalSign(kind=SignKind.UNKNOWN, status=SignStatus.STABLE,
                     modality_distribution={"radio_frequency": 1},
                     recurrence_count=1)
    res = SignUtilityEvaluator().evaluate(s)
    assert res.useful is False
    # Demoted to ambiguous, never deleted.
    assert s.status == SignStatus.AMBIGUOUS


def test_useful_sign_remains():
    s = InternalSign(kind=SignKind.MODALITY_NATIVE, status=SignStatus.STABLE,
                     modality_distribution={"radio_frequency": 5},
                     compression_utility=0.7, prediction_utility=0.7,
                     attention_utility=0.6, recurrence_count=5)
    res = SignUtilityEvaluator().evaluate(s)
    assert res.useful is True
    assert s.status == SignStatus.STABLE
