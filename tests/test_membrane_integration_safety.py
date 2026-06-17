"""Integration safety: all capabilities False, operations refused, claims guarded."""

from __future__ import annotations

from solaris_ai_nn.membrane_integration import (
    HARD_RULES,
    MembraneIntegrationSafetyValidator,
)


def test_all_capabilities_false():
    v = MembraneIntegrationSafetyValidator()
    assert v.can_actuate() is False
    assert v.can_control_hardware() is False
    assert v.can_start_feeders() is False
    assert v.can_stop_feeders() is False
    assert v.can_control_feeders() is False
    assert v.can_access_network() is False
    assert v.can_run_shell() is False
    assert v.can_run_git() is False
    assert v.can_modify_source() is False
    assert v.can_execute_commands() is False
    assert v.can_allow_silent_raw_downstream() is False
    assert v.can_promote_without_ancestry() is False
    assert v.sensory_text_is_command() is False
    assert v.human_label_is_ground_truth() is False
    assert v.debug_gloss_is_ground_truth() is False
    assert v.operator_pulse_is_teaching() is False


def test_forbidden_operations_refused():
    v = MembraneIntegrationSafetyValidator()
    for op in ("start feeder", "actuate robot arm", "git push origin",
               "open browser to url", "run command rm", "read camera",
               "raw event into ontogenesis", "hide bypass findings"):
        assert v.validate_operation(op).safe is False, op
    assert v.rejected_count >= 8


def test_bounded_runtime():
    v = MembraneIntegrationSafetyValidator()
    assert v.validate_bounded(120).safe is True
    assert v.validate_bounded(0).safe is False


def test_promotion_requires_ancestry_when_membrane_exists():
    v = MembraneIntegrationSafetyValidator()
    assert v.validate_promotion_has_ancestry(
        membrane_exists=True, has_ancestry=False).safe is False
    assert v.validate_promotion_has_ancestry(
        membrane_exists=True, has_ancestry=True).safe is True
    # No membrane: no ancestry requirement.
    assert v.validate_promotion_has_ancestry(
        membrane_exists=False, has_ancestry=False).safe is True


def test_silent_bypass_and_hidden_findings_refused():
    v = MembraneIntegrationSafetyValidator()
    assert v.validate_no_silent_bypass(True).safe is False
    assert v.validate_no_hidden_findings(True).safe is False
    assert v.validate_no_silent_bypass(False).safe is True


def test_claim_text_guard():
    v = MembraneIntegrationSafetyValidator()
    assert v.validate_claim_text(
        "The system is conscious and has free will.").safe is False
    safe = v.validate_claim_text(
        "Membrane integration is an audit layer and makes no claim of "
        "consciousness; it is not alive.")
    assert safe.safe is True


def test_snapshot_lists_hard_rules():
    v = MembraneIntegrationSafetyValidator()
    snap = v.snapshot()
    assert snap["hard_rules"] == list(HARD_RULES)
    assert "no silent raw-event downstream path" in snap["hard_rules"]
    assert snap["can_start_feeders"] is False
