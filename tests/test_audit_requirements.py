"""AuditChecklist: external audit schema; consent/firewall/governance fields."""

from __future__ import annotations

from solaris_ai_nn.pilot4_planning import AuditChecklist


def test_external_audit_schema_generated():
    a = AuditChecklist()
    assert a.field_names()
    assert a.completeness == 1.0


def test_consent_firewall_governance_fields_included():
    a = AuditChecklist()
    for field_name in ("consent_reference", "firewall_decision",
                       "governance_approval", "safety_decision",
                       "action_proposal", "human_reviewer", "emergency_state",
                       "rollback_undo_status", "evidence_refs"):
        assert a.has_field(field_name), field_name


def test_schema_does_not_apply_to_current_system():
    a = AuditChecklist()
    assert a.applies_to_current_system is False
    snap = a.snapshot()
    assert snap["applies_to_current_system"] is False
    assert "specification only" in snap["note"]
