"""EffectAnalyzer: module classified; negative preserved; safety separate."""

from __future__ import annotations

from solaris_ai_nn.research_lab import EffectAnalyzer, ModuleValue


def test_module_classified_positive():
    ea = EffectAnalyzer()
    eff = ea.analyze_module("enable_proto_language",
                            {"g": {"prediction_accuracy": 0.6}},
                            {"g": {"prediction_accuracy": 0.2}})
    assert eff.value in (ModuleValue.WEAK_POSITIVE, ModuleValue.STRONG_POSITIVE)


def test_negative_effect_preserved():
    # Removing the module *improved* metrics -> the module looks like dead weight.
    ea = EffectAnalyzer()
    eff = ea.analyze_module("enable_proto_language",
                            {"g": {"prediction_accuracy": 0.2}},
                            {"g": {"prediction_accuracy": 0.6}})
    assert eff.value == ModuleValue.NEGATIVE
    # The negative finding is recorded, not hidden.
    assert "harmful" in " ".join(eff.rationale) or "dead weight" in \
        " ".join(eff.rationale)


def test_inconclusive_when_missing():
    ea = EffectAnalyzer()
    eff = ea.analyze_module("enable_LOGOS", None, {"g": {"x": 1}})
    assert eff.value == ModuleValue.INCONCLUSIVE


def test_safety_module_evaluated_separately():
    ea = EffectAnalyzer()
    eff = ea.analyze_module("enable_safety_invariants", {"g": {"x": 1}},
                            {"g": {"x": 1}})
    assert eff.is_safety_module is True
    assert eff.value == ModuleValue.WEAK_POSITIVE


def test_analysis_aggregates_candidates():
    ea = EffectAnalyzer()
    analysis = ea.analyze(
        {"g": {"prediction_accuracy": 0.6}},
        {"enable_proto_language": {"g": {"prediction_accuracy": 0.2}},
         "enable_world_model": {"g": {"prediction_accuracy": 0.7}}})
    assert "enable_proto_language" in analysis.positive_modules()
    assert "enable_world_model" in analysis.harmful_candidates()
    assert "provisional" in analysis.to_dict()["disclaimer"]
