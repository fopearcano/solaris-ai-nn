"""Tests for the governance audit JSONL log."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.governance import audit as A


def test_jsonl_audit_writes_events(tmp_path):
    path = tmp_path / "governance_audit.jsonl"
    log = A.GovernanceAuditLog(path, run_id="r1", session_id="s1",
                               operator="alice")
    log.record(A.RISK_ASSESSED, decision="low", reason="bounded run")
    log.record(A.CHECKLIST_COMPLETED, decision="passed", reason="pre-run",
               metadata={"failed_required": []})
    rows = [json.loads(line) for line in
            path.read_text().strip().splitlines()]
    assert len(rows) == 2
    for row in rows:
        for key in ("timestamp", "run_id", "session_id", "operator",
                    "event_type", "decision", "reason", "metadata"):
            assert key in row
    assert rows[0]["run_id"] == "r1"
    assert rows[1]["event_type"] == "checklist_completed"


def test_policy_violation_recorded(tmp_path):
    log = A.GovernanceAuditLog(tmp_path / "audit.jsonl")
    log.record(A.POLICY_VIOLATION, decision="denied",
               reason="real-world actuation requested",
               metadata={"rule_id": "simulation_only_embodiment"})
    row = log.last()
    assert row["event_type"] == "policy_violation"
    assert "real-world" in row["reason"]


def test_approval_event_recorded(tmp_path):
    log = A.GovernanceAuditLog(tmp_path / "audit.jsonl")
    log.record(A.APPROVAL_REQUESTED, decision="pending", reason="soak pilot")
    log.record(A.APPROVAL_GRANTED, decision="approved", operator="alice")
    counts = log.count_by_type()
    assert counts["approval_requested"] == 1
    assert counts["approval_granted"] == 1


def test_unknown_event_type_rejected(tmp_path):
    log = A.GovernanceAuditLog(tmp_path / "audit.jsonl")
    with pytest.raises(ValueError):
        log.record("made_up_event")


def test_all_twelve_event_types_accepted(tmp_path):
    log = A.GovernanceAuditLog(tmp_path / "audit.jsonl")
    assert len(A.GOVERNANCE_AUDIT_EVENTS) == 12
    for event_type in sorted(A.GOVERNANCE_AUDIT_EVENTS):
        log.record(event_type, decision="test")
    assert len(log.read_all()) == 12


def test_log_survives_reopen(tmp_path):
    path = tmp_path / "audit.jsonl"
    first = A.GovernanceAuditLog(path)
    first.record(A.RISK_ASSESSED, decision="low")
    first.close()
    second = A.GovernanceAuditLog(path)  # append mode
    second.record(A.RISK_ASSESSED, decision="medium")
    assert len(second.read_all()) == 2
