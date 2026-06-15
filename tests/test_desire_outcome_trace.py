"""DesireOutcomeTrace: failed/blocked/no-op outcomes preserved as evidence."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import DesireOutcomeTrace, OutcomeType


def test_failed_desire_preserved():
    trace = DesireOutcomeTrace()
    trace.record(OutcomeType.DESIRE_FAILED, "DES_1")
    assert len(trace.outcomes) == 1
    note = trace.outcomes[0].to_dict()["note"]
    assert "evidence" in note and "never" in note


def test_blocked_desire_preserved():
    trace = DesireOutcomeTrace()
    trace.record(OutcomeType.DESIRE_SAFETY_BLOCKED, "DES_2")
    trace.record(OutcomeType.DESIRE_GOVERNANCE_BLOCKED, "DES_3")
    assert len(trace.outcomes) == 2


def test_no_op_preserved():
    trace = DesireOutcomeTrace()
    trace.record(OutcomeType.NO_ACTION_TAKEN, "DES_4")
    dist = trace.to_dict()["distribution"]
    assert dist[OutcomeType.NO_ACTION_TAKEN] == 1


def test_success_rate():
    trace = DesireOutcomeTrace()
    trace.record(OutcomeType.INTERNAL_ACTION_COMPLETED, "a")
    trace.record(OutcomeType.INTERNAL_ACTION_FAILED, "b")
    assert trace.success_rate() == 0.5
