"""LiveFieldSafetyValidator: hardware/network/feeder-start/mutation/live-gov."""

from __future__ import annotations

from solaris_ai_nn.live_field import HARD_RULES, LiveFieldSafetyValidator


def test_capabilities_all_false():
    v = LiveFieldSafetyValidator
    assert v.can_access_hardware() is False
    assert v.can_access_network() is False
    assert v.can_start_feeders() is False
    assert v.can_modify_source() is False
    assert v.can_actuate() is False


def test_hardware_access_blocked():
    v = LiveFieldSafetyValidator()
    assert v.validate_operation("open device driver").safe is False
    assert v.validate_operation("tune sdr").safe is False


def test_network_blocked():
    v = LiveFieldSafetyValidator()
    assert v.validate_operation("http download").safe is False


def test_feeder_auto_start_blocked():
    v = LiveFieldSafetyValidator()
    assert v.validate_operation("start feeder script").safe is False


def test_source_mutation_blocked():
    v = LiveFieldSafetyValidator()
    assert v.validate_operation("modify source file").safe is False
    assert v.validate_operation("delete source").safe is False


def test_live_without_governance_blocked():
    v = LiveFieldSafetyValidator()
    assert v.validate_live_mode(live_requested=True,
                                governance_approved=False).safe is False
    assert v.validate_live_mode(live_requested=True,
                                governance_approved=True).safe is True


def test_unbounded_polling_blocked():
    v = LiveFieldSafetyValidator()
    assert v.validate_polling_bounded(0, 0, 0).safe is False
    assert v.validate_polling_bounded(60.0, 120, 2000).safe is True


def test_hard_rules_present():
    assert "no feeder auto-start" in HARD_RULES
    assert "no live mode without governance approval" in HARD_RULES
    assert "no decoding private communications" in HARD_RULES
