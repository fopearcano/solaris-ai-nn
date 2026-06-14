"""ActionLedger: append-only, records proposal before any gate runs."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.motor_membrane import (
    ActionLedger,
    MotorAction,
    MotorActionResult,
    MotorActionStatus,
    MotorActionType,
)


def test_record_proposal_persists_jsonl(tmp_path):
    ledger = ActionLedger(state_dir=str(tmp_path))
    a = MotorAction(MotorActionType.MOVE_EAST)
    ledger.record_proposal(a, proposal_source="executive")
    assert ledger.proposed_count == 1
    assert os.path.exists(ledger.actions_path)
    lines = open(ledger.actions_path).read().splitlines()
    assert json.loads(lines[0])["action_id"] == a.action_id


def test_update_decisions_writes_firewall_log(tmp_path):
    ledger = ActionLedger(state_dir=str(tmp_path))
    a = MotorAction(MotorActionType.MOVE_EAST)
    rec = ledger.record_proposal(a)
    ledger.update_decisions(rec, firewall="allowed",
                            final_status=MotorActionStatus.EXECUTED_IN_SIMULATION)
    assert ledger.executed_count == 1
    assert os.path.exists(ledger.firewall_path)


def test_blocked_status_counted(tmp_path):
    ledger = ActionLedger(state_dir=str(tmp_path))
    a = MotorAction(MotorActionType.MOVE_EAST)
    rec = ledger.record_proposal(a)
    ledger.update_decisions(rec, final_status=MotorActionStatus.VETOED)
    assert ledger.blocked_count == 1


def test_record_result(tmp_path):
    ledger = ActionLedger(state_dir=str(tmp_path))
    r = MotorActionResult(action_id="x", action_type=MotorActionType.REST,
                          status=MotorActionStatus.EXECUTED_IN_SIMULATION)
    ledger.record_result(r)
    assert os.path.exists(ledger.results_path)


def test_write_failure_counted_without_crash():
    # No state_dir -> paths are None -> writes are skipped, no failure.
    ledger = ActionLedger(state_dir=None)
    ledger.record_proposal(MotorAction(MotorActionType.REST))
    assert ledger.write_failures == 0
    assert ledger.proposed_count == 1


def test_snapshot_exposes_paths_and_failures(tmp_path):
    ledger = ActionLedger(state_dir=str(tmp_path))
    snap = ledger.snapshot()
    assert "write_failures" in snap
    assert snap["actions_path"] == ledger.actions_path
