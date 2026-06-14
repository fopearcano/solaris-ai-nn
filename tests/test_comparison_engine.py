"""ComparisonEngine: full vs baseline; missing inconclusive; no overclaim."""

from __future__ import annotations

from solaris_ai_nn.research_lab import (
    ComparisonConfidence,
    ComparisonEngine,
    EffectDirection,
)


def test_full_vs_baseline_comparison():
    engine = ComparisonEngine()
    r = engine.compare(
        "baseline", {"g": {"prediction_accuracy": 0.0,
                           "structural_change_score": 0.05}},
        "full", {"g": {"prediction_accuracy": 0.6,
                       "structural_change_score": 0.4}})
    assert r.effect_direction == EffectDirection.IMPROVED
    assert not r.inconclusive


def test_missing_baseline_inconclusive():
    r = ComparisonEngine().compare("b", None, "full", {"g": {"x": 1}})
    assert r.inconclusive is True
    assert r.confidence == ComparisonConfidence.INCONCLUSIVE


def test_no_overlap_inconclusive():
    r = ComparisonEngine().compare("b", {"g": {"a": 1}}, "f", {"g": {"b": 2}})
    assert r.inconclusive is True


def test_single_run_is_not_high_confidence():
    r = ComparisonEngine().compare(
        "b", {"g": {"prediction_accuracy": 0.0}},
        "f", {"g": {"prediction_accuracy": 0.6}}, run_count=1)
    assert r.confidence in (ComparisonConfidence.LOW,
                            ComparisonConfidence.INCONCLUSIVE)


def test_lower_is_better_metric_direction():
    r = ComparisonEngine().compare(
        "b", {"g": {"contradiction_count": 5}},
        "f", {"g": {"contradiction_count": 1}})
    # Fewer contradictions is an improvement.
    assert r.effect_direction == EffectDirection.IMPROVED


def test_disclaimer_present():
    r = ComparisonEngine().compare("b", {"g": {"x": 1}}, "f", {"g": {"x": 2}})
    assert "not proven causal" in r.to_dict()["disclaimer"]
