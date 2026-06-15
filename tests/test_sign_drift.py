"""SignDriftDetector: meaning/source/modality drift; visible; LOGOS trigger."""

from __future__ import annotations

from solaris_ai_nn.semiogenesis import (
    InternalSign,
    SignDrift,
    SignDriftDetector,
    SignKind,
)


def test_modality_and_source_drift_detected():
    detector = SignDriftDetector()
    sign = InternalSign(kind=SignKind.MODALITY_NATIVE,
                        modality_distribution={"radio_frequency": 4},
                        source_distribution={"rf_feed": 4})
    detector.observe(sign)  # baseline
    sign.modality_distribution["vibration"] = 2
    sign.source_distribution["other_feed"] = 1
    res = detector.observe(sign)
    assert res.drifted is True
    assert SignDrift.MODALITY in res.kinds
    assert SignDrift.SOURCE in res.kinds


def test_drift_visible_in_dict():
    detector = SignDriftDetector()
    sign = InternalSign(kind=SignKind.MODALITY_NATIVE,
                        modality_distribution={"radio_frequency": 4})
    detector.observe(sign)
    sign.ambiguity_score = 0.6
    res = detector.observe(sign)
    assert "drift is made visible" in res.to_dict()["note"]
    assert SignDrift.AMBIGUITY_INCREASE in res.kinds


def test_severe_drift_triggers_logos_recommendation():
    detector = SignDriftDetector()
    sign = InternalSign(kind=SignKind.MODALITY_NATIVE,
                        modality_distribution={"radio_frequency": 4},
                        source_distribution={"rf_feed": 4})
    detector.observe(sign)
    sign.modality_distribution.update({"vibration": 2, "thermal": 1,
                                       "magnetic": 1})
    sign.source_distribution["other"] = 2
    sign.ambiguity_score = 0.8
    res = detector.observe(sign)
    assert res.severity >= 0.6
    assert res.recommend_logos_tension is True


def test_first_observation_has_no_drift():
    res = SignDriftDetector().observe(
        InternalSign(kind=SignKind.MODALITY_NATIVE,
                     modality_distribution={"radio_frequency": 2}))
    assert res.drifted is False
