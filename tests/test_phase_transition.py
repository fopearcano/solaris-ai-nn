"""PhaseTransitionDetector: evidence-backed; false-risk; missing -> inconclusive."""

from __future__ import annotations

from solaris_ai_nn.developmental_life import PhaseTransitionDetector
from solaris_ai_nn.developmental_life.growth_state import GrowthDimension


def test_transition_detected_with_evidence():
    prior = {d: 0.0 for d in GrowthDimension.ALL}
    current = dict(prior)
    current[GrowthDimension.PROTO_CONCEPT_GROWTH] = 0.5
    transitions = PhaseTransitionDetector().detect(prior_dims=prior,
                                                   current_dims=current)
    confident = [t for t in transitions if not t.inconclusive]
    assert confident
    assert confident[0].evidence


def test_false_transition_risk_tracked():
    prior = {d: 0.0 for d in GrowthDimension.ALL}
    current = dict(prior)
    current[GrowthDimension.SIGN_GROWTH] = 0.3
    t = [x for x in PhaseTransitionDetector().detect(prior_dims=prior,
                                                     current_dims=current)
         if not x.inconclusive][0]
    assert 0.0 <= t.false_transition_risk <= 1.0
    assert t.confidence_band in ("low", "moderate", "high")


def test_missing_evidence_inconclusive():
    prior = {GrowthDimension.PROTO_CONCEPT_GROWTH: 0.0}
    current = {GrowthDimension.PROTO_CONCEPT_GROWTH: 0.0}  # other dims missing
    transitions = PhaseTransitionDetector().detect(prior_dims=prior,
                                                   current_dims=current)
    assert any(t.inconclusive for t in transitions)


def test_no_prior_no_transitions():
    transitions = PhaseTransitionDetector().detect(prior_dims={},
                                                   current_dims={"x": 1.0})
    assert transitions == []
