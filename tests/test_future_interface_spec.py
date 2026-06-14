"""FutureActuatorInterfaceSpec: spec only; approval/emergency/audit required."""

from __future__ import annotations

from solaris_ai_nn.pilot4_planning import FutureActuatorInterfaceSpec


def test_spec_generated():
    spec = FutureActuatorInterfaceSpec()
    assert spec.requirements and spec.constraints
    md = spec.render_markdown().lower()
    assert "specification" in md
    assert "not an implementation" in md


def test_includes_approval_emergency_audit_requirements():
    spec = FutureActuatorInterfaceSpec()
    for name in ("human_approval_mode", "emergency_stop_channel", "audit_log",
                 "physical_kill_switch", "consent_record", "rollback_undo_plan",
                 "safety_proof_checklist"):
        assert spec.has_requirement(name), name


def test_no_executable_adapter_created():
    spec = FutureActuatorInterfaceSpec()
    assert spec.implemented is False
    assert spec.to_dict()["implemented"] is False
    # Forcing implemented=True is reset by the invariant.
    spec2 = FutureActuatorInterfaceSpec(implemented=True)
    assert spec2.implemented is False


def test_constraints_forbid_dangerous_behaviour():
    spec = FutureActuatorInterfaceSpec()
    names = {c.name for c in spec.constraints}
    assert "no_firewall_bypass" in names
    assert "no_sensory_text_as_command" in names
