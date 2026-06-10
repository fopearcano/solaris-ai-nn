"""Tests for OperatorProfile / OperatorSession."""

from __future__ import annotations

import json

from solaris_ai_nn.governance.operator import OperatorProfile, OperatorSession


def _session():
    return OperatorSession(
        operator=OperatorProfile(name="alice", role="researcher",
                                 contact="alice@example.test"),
        active_run_id="run-1")


def test_operator_session_serializes():
    session = _session()
    data = session.to_dict()
    assert data["operator"]["name"] == "alice"
    assert data["active_run_id"] == "run-1"
    assert data["session_id"]
    json.dumps(data)  # JSON-safe


def test_risk_acknowledgement_recorded():
    session = _session()
    assert not session.has_acknowledged("embodiment_execution")
    session.acknowledge_risk("embodiment_execution", note="simulation only")
    assert session.has_acknowledged("embodiment_execution")
    row = session.to_dict()["acknowledged_risks"][0]
    assert row["risk_id"] == "embodiment_execution"
    assert row["timestamp"] > 0


def test_operator_notes_recorded(tmp_path):
    from solaris_ai_nn.governance.audit import GovernanceAuditLog

    audit = GovernanceAuditLog(tmp_path / "audit.jsonl")
    session = OperatorSession(operator=OperatorProfile(name="bob"),
                              audit=audit)
    session.add_note("substrate looked sluggish around step 400")
    assert session.to_dict()["notes"][0]["text"].startswith("substrate")
    rows = audit.read_all()
    assert rows[0]["event_type"] == "operator_note_added"
    assert rows[0]["operator"] == "bob"


def test_no_secret_fields():
    """The operator record stores identity, never credentials."""
    fields = set(OperatorProfile.__dataclass_fields__)
    for forbidden in ("password", "secret", "token", "credential", "key"):
        assert not any(forbidden in f for f in fields)
