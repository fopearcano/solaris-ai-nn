"""Operator decisions: never auto-approved/invented; rejection preserved."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import (
    OperatorDecisionStatus,
    OperatorDecisionType,
    load_operator_decisions,
    required_decisions,
)


def test_records_never_auto_approved_or_invented():
    recs = load_operator_decisions([
        {"decision_type": "confirm_external_merge", "status": "approved"}])
    d = recs[0].to_dict()
    assert d["auto_approved"] is False
    assert d["invented_by_system"] is False
    assert d["approved"] is True


def test_rejection_preserved():
    recs = load_operator_decisions([
        {"decision_type": "reject_merge", "status": "rejected"}])
    assert recs[0].rejected is True


def test_unknown_decision_type_normalized():
    recs = load_operator_decisions([
        {"decision_type": "nonsense", "status": "approved"}])
    assert recs[0].decision_type == OperatorDecisionType.REQUEST_REVISION


def test_required_decisions_until_explicitly_made():
    bundle = {"experiment_compiler": {"x": 1},
              "implementation_intake": {"x": 1}, "post_merge": {"x": 1}}
    reqs = required_decisions(bundle, [])
    types = {r.decision_type for r in reqs}
    assert OperatorDecisionType.CONFIRM_EXTERNAL_MERGE in types
    assert OperatorDecisionType.APPROVE_CANDIDATE_BASELINE in types
    # Once made, no longer required.
    made = load_operator_decisions([
        {"decision_type": "confirm_external_merge", "status": "approved"},
        {"decision_type": "approve_candidate_baseline", "status": "approved"}])
    reqs2 = {r.decision_type for r in required_decisions(bundle, made)}
    assert OperatorDecisionType.CONFIRM_EXTERNAL_MERGE not in reqs2
    assert OperatorDecisionType.APPROVE_CANDIDATE_BASELINE not in reqs2


def test_pending_does_not_count_as_made():
    bundle = {"post_merge": {"x": 1}}
    made = load_operator_decisions([
        {"decision_type": "approve_candidate_baseline",
         "status": OperatorDecisionStatus.PENDING}])
    reqs = {r.decision_type for r in required_decisions(bundle, made)}
    assert OperatorDecisionType.APPROVE_CANDIDATE_BASELINE in reqs
