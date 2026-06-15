"""ReadinessGate: gates work; safety block; governance required."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import (
    DesireCandidate,
    DesireKind,
    ReadinessGate,
    ReadinessState,
)


def test_ready_when_all_gates_pass():
    d = DesireCandidate(kind=DesireKind.COMPARE_MODALITIES, confidence=0.8,
                        uncertainty=0.2)
    r = ReadinessGate().evaluate(d)
    assert r.state == ReadinessState.READY
    assert r.is_ready is True


def test_insufficient_evidence():
    d = DesireCandidate(kind=DesireKind.TEST_PREDICTION, confidence=0.05)
    r = ReadinessGate().evaluate(d)
    assert r.state == ReadinessState.INSUFFICIENT_EVIDENCE


def test_safety_block():
    d = DesireCandidate(kind=DesireKind.COMPARE_MODALITIES, confidence=0.8)
    r = ReadinessGate().evaluate(d, safety_ok=False)
    assert r.state == ReadinessState.SAFETY_BLOCKED


def test_governance_required():
    d = DesireCandidate(kind=DesireKind.REQUEST_OPERATOR_REVIEW, confidence=0.8)
    r = ReadinessGate().evaluate(d, governance_ok=False)
    assert r.state == ReadinessState.GOVERNANCE_REQUIRED


def test_defer_on_poor_boundary_clarity():
    d = DesireCandidate(kind=DesireKind.COMPARE_MODALITIES, confidence=0.8)
    r = ReadinessGate().evaluate(d, boundary_clear=False)
    assert r.state == ReadinessState.DEFER
    assert "cannot bypass arbitration" in r.to_dict()["note"]
