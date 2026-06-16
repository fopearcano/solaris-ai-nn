"""Blocked states: detection, critical-safety flag, resolver advice only."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import (
    BlockedReason,
    BlockedStateResolver,
    ResolverRecommendation,
)


def test_safety_regression_is_critical():
    states = BlockedStateResolver().detect({
        "implementation_intake": {"critical_safety_regression_count": 1}})
    assert any(s.reason == BlockedReason.SAFETY_GATE_FAILED
               and s.critical_safety for s in states)


def test_falsified_claim_blocks():
    states = BlockedStateResolver().detect({
        "falsification": {"falsified_claim_count": 1}})
    assert any(s.reason == BlockedReason.FALSIFIED_PROPOSAL for s in states)


def test_regression_recommends_rollback_review():
    states = BlockedStateResolver().detect({
        "post_merge": {"critical_regression_count": 2}})
    rec = [s for s in states if s.reason == BlockedReason.REGRESSION_DETECTED][0]
    assert rec.recommendation == ResolverRecommendation.ROLLBACK_REVIEW


def test_operator_rejection_blocks():
    states = BlockedStateResolver().detect({}, operator_decisions=[
        {"decision_type": "reject_merge", "status": "rejected"}])
    assert any(s.reason == BlockedReason.OPERATOR_REJECTION for s in states)


def test_critical_safety_cannot_bypass_and_executes_nothing():
    states = BlockedStateResolver().detect({
        "implementation_intake": {"critical_safety_regression_count": 1}})
    d = states[0].to_dict()
    assert d["can_bypass"] is False
    assert d["executed"] is False
    summary = BlockedStateResolver.summary(states)
    assert summary["critical_safety_blocker_count"] >= 1


def test_clean_bundle_has_no_blockers():
    assert BlockedStateResolver().detect({
        "research_baseline": {"baseline_status": "validated"}}) == []
