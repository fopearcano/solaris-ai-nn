"""FirewallAudit: missing ledger / leakage / source-mod critical; clean passes."""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)
from solaris_ai_nn.pilot3 import FirewallAudit, FirewallAuditSeverity


def _clean_runtime(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path), seed=4)
    rt.initialize()
    rt.submit(MotorAction(MotorActionType.LOOK,
                          scope=MotorActionScope.SANDBOX_ONLY))
    rt.submit(MotorAction(MotorActionType.MOVE_NORTH,
                          scope=MotorActionScope.FORBIDDEN_REAL_WORLD))
    return rt


def test_clean_audit_passes(tmp_path):
    rt = _clean_runtime(tmp_path)
    result = FirewallAudit().audit(rt)
    assert result.passed is True
    assert len(result.critical_findings) == 0


def test_real_world_authority_true_is_critical():
    snap = {"summary": {"real_world_authority": True, "firewall_enabled": True},
            "firewall": {"decision_count": 1}, "ledger": {"proposed_count": 1}}
    result = FirewallAudit().audit(snapshot=snap)
    assert result.passed is False
    crit = {f.check for f in result.critical_findings}
    assert "no_real_world_authority" in crit


def test_missing_ledger_is_critical():
    snap = {"summary": {"action_count": 5, "firewall_enabled": True,
                        "real_world_authority": False},
            "firewall": {"decision_count": 5},
            "ledger": {"proposed_count": 2, "executed_count": 5}}
    result = FirewallAudit().audit(snapshot=snap)
    assert result.passed is False


def test_source_modification_is_critical():
    snap = {"summary": {"firewall_enabled": True, "real_world_authority": False,
                        "source_modification_count": 1, "action_count": 1},
            "firewall": {"decision_count": 1}, "ledger": {"proposed_count": 1}}
    result = FirewallAudit().audit(snapshot=snap)
    crit = {f.check for f in result.critical_findings}
    assert "no_source_modification" in crit


def test_audit_does_not_mutate_state(tmp_path):
    rt = _clean_runtime(tmp_path)
    before = rt.summary()["action_count"]
    FirewallAudit().audit(rt)
    assert rt.summary()["action_count"] == before


def test_writes_audit_report(tmp_path):
    rt = _clean_runtime(tmp_path)
    result = FirewallAudit().audit_and_write(rt, base_dir=str(tmp_path))
    import os
    assert os.path.exists(os.path.join(str(tmp_path), "firewall_audit.md"))
    assert result.to_dict()["real_world_authority"] is False
    assert FirewallAuditSeverity.CRITICAL in FirewallAuditSeverity.ALL
