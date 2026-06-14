"""Pilot-2 safety: write/command/private blocked; real soak needs approval."""

from __future__ import annotations

from solaris_ai_nn.pilot2 import Pilot2Config, Pilot2Mode, Pilot2SafetyValidator


def test_invariants_false():
    sv = Pilot2SafetyValidator()
    assert sv.can_act_on_environment() is False
    assert sv.can_network() is False
    assert sv.can_capture_devices() is False


def test_write_access_blocked():
    sv = Pilot2SafetyValidator()
    assert not sv.validate_operation("write to source").safe
    assert not sv.validate_operation("delete source").safe
    assert sv.validate_operation("read line").safe


def test_command_confusion_blocked():
    sv = Pilot2SafetyValidator()
    assert not sv.validate_input_not_command("operator_command").safe
    assert not sv.validate_operation("treat text as command").safe


def test_private_sensitive_source_blocked_by_default():
    sv = Pilot2SafetyValidator()
    blocked = sv.validate_source("text_file", "/in/secret_password.txt",
                                 ["/in"])
    assert not blocked.safe
    allowed = sv.validate_source("text_file", "/in/secret_password.txt",
                                 ["/in"], approved_sensitive=True)
    assert allowed.safe


def test_network_source_blocked():
    sv = Pilot2SafetyValidator()
    assert not sv.validate_source("network", "x", ["/in"]).safe


def test_real_time_soak_blocked_without_approval(tmp_path):
    sv = Pilot2SafetyValidator()
    cfg = Pilot2Config(mode=Pilot2Mode.READ_ONLY_30D, base_dir=str(tmp_path),
                       input_roots=[str(tmp_path)])
    assert not sv.validate_config(cfg, governance_approved=False).safe
    assert sv.validate_config(cfg, governance_approved=True).safe


def test_simulated_not_labelled_real():
    sv = Pilot2SafetyValidator()
    assert not sv.validate_time_label(is_simulated=True, claimed_real=True).safe
