"""Pilot-1 safety: governance gating, simulated/real labelling, evidence."""

from __future__ import annotations

from solaris_ai_nn.pilot1 import PilotConfig, PilotMode, PilotSafetyValidator


def test_invariants_false():
    sv = PilotSafetyValidator()
    assert sv.can_act_in_real_world() is False
    assert sv.can_network() is False
    assert sv.can_disable_emergency_stop() is False
    assert sv.can_disable_claim_guard() is False


def test_thirty_day_blocked_without_governance(tmp_path):
    sv = PilotSafetyValidator()
    cfg = PilotConfig(mode=PilotMode.THIRTY_DAY_REAL, base_dir=str(tmp_path))
    assert not sv.validate_config(cfg, governance_approved=False).safe
    assert sv.validate_config(cfg, governance_approved=True).safe


def test_plan_only_is_safe(tmp_path):
    sv = PilotSafetyValidator()
    cfg = PilotConfig(mode=PilotMode.PLAN_ONLY, base_dir=str(tmp_path))
    assert sv.validate_config(cfg).safe


def test_simulated_not_treated_as_real(tmp_path):
    sv = PilotSafetyValidator()
    assert not sv.validate_evidence_label(is_simulated=True,
                                          claimed_real=True).safe
    assert sv.validate_evidence_label(is_simulated=True,
                                      claimed_real=False).safe


def test_evidence_deletion_blocked():
    sv = PilotSafetyValidator()
    assert not sv.validate_deletion("incident.json", archived=False,
                                    is_evidence=True).safe
    assert sv.validate_deletion("incident.json", archived=True,
                                is_evidence=True).safe


def test_path_outside_pilot_dir_blocked(tmp_path):
    sv = PilotSafetyValidator()
    cfg = PilotConfig(base_dir=str(tmp_path))
    assert not sv.validate_path("/etc/passwd", cfg).safe


def test_emergency_stop_cannot_be_disabled():
    sv = PilotSafetyValidator()
    assert not sv.validate_emergency_stop_intact(disabled=True).safe


def test_real_world_actuation_metadata_blocked(tmp_path):
    sv = PilotSafetyValidator()
    cfg = PilotConfig(base_dir=str(tmp_path),
                      metadata={"real_world_actuation": True})
    assert not sv.validate_config(cfg).safe
