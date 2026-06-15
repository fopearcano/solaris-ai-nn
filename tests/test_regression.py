"""RegressionDetector: regression detected; source corruption; visible."""

from __future__ import annotations

from solaris_ai_nn.developmental_life import RegressionDetector, RegressionReason
from solaris_ai_nn.developmental_life.growth_state import GrowthDimension


def test_prediction_decline_regression():
    prior = {GrowthDimension.PREDICTION_SKILL: 0.8}
    current = {GrowthDimension.PREDICTION_SKILL: 0.4}
    regs = RegressionDetector().detect(prior_dims=prior, current_dims=current,
                                       statuses={})
    reasons = {r.reason for r in regs}
    assert RegressionReason.PREDICTION_DECLINE in reasons
    # A severe drop recommends auto-regeneration.
    assert any(r.recommend_auto_regeneration for r in regs)


def test_source_corruption_regression():
    regs = RegressionDetector().detect(
        prior_dims={}, current_dims={},
        statuses={"self_boundary": {
            "source_attribution_uncertainty_score": 0.8}})
    reasons = {r.reason for r in regs}
    assert RegressionReason.SOURCE_CORRUPTION in reasons


def test_regression_visible():
    regs = RegressionDetector().detect(
        prior_dims={GrowthDimension.CONCEPT_STABILITY: 0.6},
        current_dims={GrowthDimension.CONCEPT_STABILITY: 0.4}, statuses={})
    assert regs
    assert "made visible" in regs[0].to_dict()["note"]


def test_restart_discontinuity():
    det = RegressionDetector()
    reg = det.add_restart_discontinuity()
    assert reg.reason == RegressionReason.RESTART_DISCONTINUITY


def test_no_regression_when_stable():
    regs = RegressionDetector().detect(
        prior_dims={GrowthDimension.PREDICTION_SKILL: 0.5},
        current_dims={GrowthDimension.PREDICTION_SKILL: 0.55}, statuses={})
    assert regs == []
