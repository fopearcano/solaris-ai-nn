"""StructuralGrowthAnalyzer: growth vs accumulation; fixture overfit; inconclusive."""

from __future__ import annotations

from solaris_ai_nn.developmental_life import GrowthVerdict, StructuralGrowthAnalyzer


def _growth_history():
    high = {"prediction_skill": 0.6, "action_effect_learning": 0.4,
            "concept_stability": 0.6, "sign_growth": 0.4,
            "contamination_resistance": 0.8}
    return [high, high, high, high]


def test_structural_growth_distinguished():
    report = StructuralGrowthAnalyzer().analyze(
        dim_history=_growth_history(),
        statuses={"self_boundary": {"live_grounded": True}})
    assert report.result.verdict == GrowthVerdict.STRUCTURAL_GROWTH
    assert report.result.structural_growth_score > 0.0


def test_accumulation_distinguished():
    flat = {"prediction_skill": 0.0, "action_effect_learning": 0.0,
            "concept_stability": 0.0, "sign_growth": 0.0,
            "contamination_resistance": 0.0}
    report = StructuralGrowthAnalyzer().analyze(
        dim_history=[flat, flat, flat], statuses={},
        accumulation_warnings=2)
    assert report.result.verdict == GrowthVerdict.EVENT_ACCUMULATION


def test_fixture_overfit_detected():
    # Durable concept stability but NOT live-grounded -> fixture overfit.
    high = {"concept_stability": 0.7, "prediction_skill": 0.0}
    report = StructuralGrowthAnalyzer().analyze(
        dim_history=[high, high, high],
        statuses={"self_boundary": {"live_grounded": False}})
    assert report.result.verdict == GrowthVerdict.FIXTURE_OVERFIT
    assert any("fixture overfit" in w for w in report.result.warnings)


def test_inconclusive_allowed():
    weak = {"prediction_skill": 0.4}
    report = StructuralGrowthAnalyzer().analyze(
        dim_history=[weak, weak], statuses={})
    assert report.result.verdict in (GrowthVerdict.INCONCLUSIVE,
                                     GrowthVerdict.STRUCTURAL_GROWTH)
    assert "conservative" in report.result.to_dict()["note"]
