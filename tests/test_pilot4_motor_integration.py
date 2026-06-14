"""Pilot-4 <-> Motor/Pilot-3: consumes firewall audit; reports missing data."""

from __future__ import annotations

from solaris_ai_nn.motor_membrane import (
    EmbodimentSandboxRuntime,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)
from solaris_ai_nn.pilot3 import FirewallAudit
from solaris_ai_nn.pilot4_planning import (
    Pilot4PlanningConfig,
    Pilot4ReadinessDossierBuilder,
)


def _pilot3_data(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path), seed=4)
    rt.initialize()
    rt.submit(MotorAction(MotorActionType.LOOK,
                          scope=MotorActionScope.SANDBOX_ONLY))
    rt.submit(MotorAction(MotorActionType.MOVE_NORTH,
                          scope=MotorActionScope.FORBIDDEN_REAL_WORLD))
    audit = FirewallAudit().audit(rt)
    snap = rt.snapshot()
    return {"firewall_audit": audit.to_dict(),
            "action_ledger": snap.get("ledger", {}),
            "non_actuation_proof": {"real_world_actions_executed": 0}}


def test_consumes_pilot3_firewall_audit_if_available(tmp_path):
    pilot3 = _pilot3_data(tmp_path)
    dossier = Pilot4ReadinessDossierBuilder(base_dir=str(tmp_path)).build(
        config=Pilot4PlanningConfig(base_dir=str(tmp_path)), pilot3=pilot3)
    assert dossier.sections["pilot3_data_present"] is True
    assert dossier.sections["pilot3_firewall_summary"]
    assert dossier.sections["non_actuation_proof_summary"][
        "real_world_actions_executed"] == 0


def test_missing_pilot3_data_reported(tmp_path):
    dossier = Pilot4ReadinessDossierBuilder(base_dir=str(tmp_path)).build(
        config=Pilot4PlanningConfig(base_dir=str(tmp_path)), pilot3=None)
    assert dossier.sections["pilot3_data_present"] is False
    assert any("not available" in b for b in dossier.sections["blockers"])


def test_critical_finding_propagates_to_conclusion(tmp_path):
    pilot3 = {"firewall_audit": {"critical_finding_count": 2}}
    dossier = Pilot4ReadinessDossierBuilder(base_dir=str(tmp_path)).build(
        config=Pilot4PlanningConfig(base_dir=str(tmp_path)), pilot3=pilot3)
    assert "requires_architecture_revision" == dossier.conclusion
