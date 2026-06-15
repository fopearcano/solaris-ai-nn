"""EffectLearningEngine: repeated effect strengthens; failures visible; not cause."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import EffectLearningEngine


def test_repeated_effect_strengthens_confidence():
    engine = EffectLearningEngine()
    for _ in range(4):
        engine.observe("shift_attention", "uncertainty_reduced", "constructive")
    model = engine.models["shift_attention"]
    assert model.observations == 4
    assert model.confidence > 0.5
    assert model.success_rate == 1.0


def test_failed_effect_visible():
    engine = EffectLearningEngine()
    engine.observe("test_internal_prediction", "prediction_failed", "disruptive")
    engine.observe("test_internal_prediction", "prediction_failed", "disruptive")
    model = engine.models["test_internal_prediction"]
    assert model.success_rate < 0.3
    assert "test_internal_prediction" in engine.low_effect_actions()


def test_correlation_not_causation():
    engine = EffectLearningEngine()
    engine.observe("shift_attention", "uncertainty_reduced", "constructive")
    note = engine.models["shift_attention"].to_dict()["note"]
    assert "correlation is not causation" in note


def test_learned_count_requires_repeated_evidence():
    engine = EffectLearningEngine()
    engine.observe("shift_attention", "uncertainty_reduced", "constructive")
    assert engine.learned_count() == 0  # one observation is not "learned"
    engine.observe("shift_attention", "uncertainty_reduced", "constructive")
    assert engine.learned_count() == 1
