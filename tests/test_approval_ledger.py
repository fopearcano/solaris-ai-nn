"""ApprovalLedger: appended; forbidden blocked; cannot disable safety."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.operator_console import ApprovalLedger, ApprovalScope


def test_approval_record_appended(tmp_path):
    ledger = ApprovalLedger(state_dir=str(tmp_path / "op"))
    record = ledger.record(ApprovalScope.BOUNDED_FIXTURE_RUN, "ok to run")
    assert record.recorded
    assert os.path.isfile(ledger.path)
    lines = open(ledger.path, encoding="utf-8").read().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["scope"] == ApprovalScope.BOUNDED_FIXTURE_RUN


def test_forbidden_real_world_approval_blocked(tmp_path):
    ledger = ApprovalLedger(state_dir=str(tmp_path / "op"))
    record = ledger.record(ApprovalScope.FORBIDDEN_REAL_WORLD_ACTUATION, "no")
    assert record.recorded is False
    assert record.status == "blocked"
    assert ledger.blocked_count() == 1


def test_unknown_scope_blocked(tmp_path):
    ledger = ApprovalLedger(state_dir=str(tmp_path / "op"))
    record = ledger.record("approve_everything", "no")
    assert record.recorded is False


def test_approval_cannot_disable_safety(tmp_path):
    ledger = ApprovalLedger(state_dir=str(tmp_path / "op"))
    record = ledger.record(ApprovalScope.BOUNDED_FIXTURE_RUN, "ok")
    text = " ".join(record.limitations).lower()
    assert "no approval can disable safety" in text
    assert "no approval can enable forbidden real-world actuation" in text
