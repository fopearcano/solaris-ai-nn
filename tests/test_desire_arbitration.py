"""DesireArbitrator: internal action selected; no-op selected; unsafe blocked."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import (
    ArbitrationOutcome,
    DesireArbitrator,
    DesireCandidate,
    DesireKind,
    ReadinessGate,
)


def _arbitrate(desire, *, overloaded=False, safety_ok=True):
    readiness = ReadinessGate().evaluate(desire, safety_ok=safety_ok)
    return DesireArbitrator().arbitrate(desire, readiness,
                                        overloaded=overloaded,
                                        safety_ok=safety_ok)


def test_internal_action_selected():
    d = DesireCandidate(kind=DesireKind.COMPARE_MODALITIES, confidence=0.8,
                        expected_utility=0.8, urgency=0.7)
    res = _arbitrate(d)
    assert res.outcome in (ArbitrationOutcome.SELECT_INTERNAL_ACTION,
                           ArbitrationOutcome.SELECT_ATTENTION_SHIFT,
                           ArbitrationOutcome.SELECT_SIMULATION,
                           ArbitrationOutcome.SELECT_CONSOLIDATION)
    assert res.selected_action


def test_no_op_selected_on_overload():
    d = DesireCandidate(kind=DesireKind.FOCUS_MODALITY, confidence=0.8,
                        expected_utility=0.8)
    res = _arbitrate(d, overloaded=True)
    assert res.outcome == ArbitrationOutcome.NO_OP


def test_no_action_desire_is_no_op():
    d = DesireCandidate(kind=DesireKind.NO_ACTION)
    res = _arbitrate(d)
    assert res.outcome == ArbitrationOutcome.NO_OP


def test_unsafe_action_blocked():
    d = DesireCandidate(kind=DesireKind.COMPARE_MODALITIES, confidence=0.9)
    res = _arbitrate(d, safety_ok=False)
    assert res.outcome == ArbitrationOutcome.SAFETY_BLOCK
    assert "safety/governance have veto" in res.to_dict()["note"]
