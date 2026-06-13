"""Tests for hypothesis prioritization."""

from __future__ import annotations

from solaris_ai_nn.hypothesis.hypotheses import (
    Hypothesis,
    HypothesisStatus,
    HypothesisType,
)
from solaris_ai_nn.hypothesis.priority import HypothesisPrioritizer


def _hyp(htype=HypothesisType.MYSTERIUM_REDUCTION, risk="low", target="t",
         testable=True, status=HypothesisStatus.PROPOSED):
    h = Hypothesis(type=htype, statement="s", target_ref=target,
                   risk_level=risk, testable=testable, status=status,
                   uncertainty=0.7)
    return h


def test_low_risk_high_info_ranks_high():
    prio = HypothesisPrioritizer()
    low_risk = _hyp(risk="low", target="a")
    high_risk = _hyp(risk="high", target="b")
    ranked = prio.prioritize([high_risk, low_risk],
                             {"mysterium_pressure": 0.8})
    assert ranked[0] is low_risk


def test_unsafe_hypothesis_not_scheduled():
    prio = HypothesisPrioritizer()
    unsafe = _hyp(status=HypothesisStatus.UNSAFE_TO_TEST, testable=False)
    ranked = prio.prioritize([unsafe], {})
    assert unsafe not in ranked
    assert prio.score(unsafe, {}) == 0.0


def test_emergency_blocks_testing():
    prio = HypothesisPrioritizer()
    h = _hyp()
    assert prio.testing_blocked({"emergency": True})
    ranked = prio.prioritize([h], {"emergency": True})
    assert ranked == []


def test_critical_health_blocks_testing():
    prio = HypothesisPrioritizer()
    assert prio.testing_blocked({"health_level": "critical"})


def test_closed_hypothesis_not_scheduled():
    prio = HypothesisPrioritizer()
    h = _hyp(status=HypothesisStatus.FALSIFIED)
    ranked = prio.prioritize([h], {})
    assert h not in ranked
