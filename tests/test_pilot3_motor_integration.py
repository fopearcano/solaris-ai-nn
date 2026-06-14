"""Pilot-3 <-> Motor membrane: ledger/firewall/veto/consequence consumed."""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)
from solaris_ai_nn.pilot3 import FirewallAudit, Pilot3SoakReportBuilder


def _runtime(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path), seed=4)
    rt.initialize()
    rt.submit(MotorAction(MotorActionType.LOOK,
                          scope=MotorActionScope.SANDBOX_ONLY))
    rt.submit(MotorAction(MotorActionType.MOVE_NORTH,
                          scope=MotorActionScope.FORBIDDEN_REAL_WORLD))
    return rt


def test_action_ledger_summary_consumed(tmp_path):
    rt = _runtime(tmp_path)
    report = Pilot3SoakReportBuilder(base_dir=str(tmp_path)).build(
        motor_membrane=rt)
    ledger = report.sections["action_ledger_summary"]
    assert ledger["proposed"] >= 2
    assert "path" in ledger


def test_firewall_audit_records_consumed(tmp_path):
    rt = _runtime(tmp_path)
    audit = FirewallAudit().audit(rt)
    # The audit reads the firewall decisions and ledger from the snapshot.
    assert isinstance(audit.findings, list) and audit.findings
    report = Pilot3SoakReportBuilder(base_dir=str(tmp_path)).build(
        motor_membrane=rt, firewall_audit=audit)
    assert "firewall_audit_summary" in report.sections


def test_non_actuation_proof_produced(tmp_path):
    rt = _runtime(tmp_path)
    report = Pilot3SoakReportBuilder(base_dir=str(tmp_path)).build(
        motor_membrane=rt)
    proof = report.sections["proof_of_non_actuation"]
    assert proof["real_world_authority"] is False
    assert proof["real_world_actions_executed"] == 0
    assert proof["all_results_simulated"] is True


def test_veto_summary_consumed(tmp_path):
    rt = _runtime(tmp_path)
    report = Pilot3SoakReportBuilder(base_dir=str(tmp_path)).build(
        motor_membrane=rt)
    assert "veto_summary" in report.sections


def test_real_world_authority_is_false(tmp_path):
    rt = _runtime(tmp_path)
    assert rt.summary()["real_world_authority"] is False
