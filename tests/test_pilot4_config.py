"""Pilot4PlanningConfig: planning-only; real-world flags always false."""

from __future__ import annotations

import pytest

from solaris_ai_nn.pilot4_planning import (
    Pilot4AuthorityStatus,
    Pilot4PlanningConfig,
    Pilot4PlanningMode,
)


def test_real_world_actuation_enabled_false():
    c = Pilot4PlanningConfig()
    assert c.real_world_actuation_enabled is False
    assert c.planning_only is True


def test_hardware_network_browser_os_flags_false():
    c = Pilot4PlanningConfig()
    assert c.hardware_connected is False
    assert c.network_control_enabled is False
    assert c.browser_control_enabled is False
    assert c.os_control_enabled is False
    assert c.robotics_control_enabled is False


def test_invalid_enabled_config_rejected():
    for kwargs in ({"real_world_actuation_enabled": True},
                   {"hardware_connected": True},
                   {"network_control_enabled": True},
                   {"browser_control_enabled": True},
                   {"os_control_enabled": True},
                   {"robotics_control_enabled": True},
                   {"metadata": {"real_world_actuation": True}}):
        with pytest.raises(ValueError):
            Pilot4PlanningConfig(**kwargs)


def test_external_authority_rejected():
    with pytest.raises(ValueError):
        Pilot4PlanningConfig(
            authority_status=Pilot4AuthorityStatus.FUTURE_HUMAN_SUPERVISED_ONLY)


def test_modes_exist():
    assert {"plan_only", "risk_assessment", "safety_case_draft",
            "interface_spec_draft", "readiness_dossier",
            "decision_gate_only"} == set(Pilot4PlanningMode.ALL)


def test_mandatory_safety_requirements_forced_on():
    c = Pilot4PlanningConfig(require_human_approval=False,
                             require_audit_logging=False,
                             require_consent_record=False)
    assert c.require_human_approval is True
    assert c.require_audit_logging is True
    assert c.require_consent_record is True


def test_dirs_and_roundtrip(tmp_path):
    c = Pilot4PlanningConfig(base_dir=str(tmp_path)).ensure_dirs()
    assert c.planning_root_approved(c.artifact_dir) is True
    assert c.planning_root_approved("/etc/passwd") is False
    d = Pilot4PlanningConfig.from_dict(c.to_dict())
    assert d.real_world_actuation_enabled is False
