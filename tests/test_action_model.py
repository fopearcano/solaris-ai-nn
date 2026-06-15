"""ActionCandidateRecord: serializes; forbidden external blocked; no-op valid."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import (
    ActionCandidateRecord,
    ActionKind,
    ActionScope,
)


def test_action_candidate_serializes():
    a = ActionCandidateRecord(kind=ActionKind.SHIFT_ATTENTION, desire_ref="D1")
    d = a.to_dict()
    assert d["kind"] == ActionKind.SHIFT_ATTENTION
    assert d["scope"] == ActionScope.INTERNAL_ONLY
    assert "no real-world actuation" in d["note"]


def test_forbidden_external_scope_blocked():
    a = ActionCandidateRecord(kind="actuate_robot")
    assert a.is_forbidden is True
    assert a.scope == ActionScope.FORBIDDEN_EXTERNAL


def test_no_op_is_valid():
    a = ActionCandidateRecord(kind=ActionKind.NO_OP)
    assert a.is_no_op is True
    assert a.is_forbidden is False
    assert a.scope == ActionScope.INTERNAL_ONLY


def test_simulation_and_governance_scopes():
    sim = ActionCandidateRecord(kind=ActionKind.RUN_BOUNDED_SIMULATION)
    gov = ActionCandidateRecord(kind=ActionKind.REQUEST_OPERATOR_REVIEW)
    assert sim.scope == ActionScope.SIMULATION_ONLY
    assert gov.scope == ActionScope.GOVERNANCE_RECORD_ONLY


def test_evidence_chain_present():
    a = ActionCandidateRecord(kind=ActionKind.COMPARE_MODALITIES,
                              desire_ref="D1", push_refs=["P1"],
                              valence_refs=["V1"], readiness_ref="R1",
                              arbitration_ref="A1")
    d = a.to_dict()
    assert d["desire_ref"] == "D1"
    assert d["push_refs"] == ["P1"]
    assert d["arbitration_ref"] == "A1"
