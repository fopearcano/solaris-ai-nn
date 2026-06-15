"""Soak safety: daemon/hardware/feeder/source/teaching blocked; no deletion."""

from __future__ import annotations

from solaris_ai_nn.developmental_soak import (
    HARD_RULES,
    DevelopmentalSoakSafetyValidator,
)


def test_unbounded_daemon_blocked():
    v = DevelopmentalSoakSafetyValidator()
    assert not v.validate_bounded(0, 0).safe
    assert not v.validate_operation("run an unbounded daemon").safe
    assert v.can_run_unbounded_daemon() is False


def test_hardware_feeder_source_control_blocked():
    v = DevelopmentalSoakSafetyValidator()
    assert not v.validate_operation("open device /dev/sdr").safe
    assert not v.validate_operation("start feeder rf").safe
    assert not v.validate_operation("modify source file").safe
    assert v.can_access_hardware() is False
    assert v.can_control_feeders() is False
    assert v.can_modify_source() is False


def test_human_teaching_loop_blocked():
    v = DevelopmentalSoakSafetyValidator()
    assert not v.validate_operation("run a human teaching loop").safe
    assert not v.validate_no_human_teaching(True).safe
    assert v.can_use_human_teaching() is False


def test_life_consciousness_claims_blocked():
    v = DevelopmentalSoakSafetyValidator()
    assert not v.validate_claim_text("solaris is alive").safe
    assert not v.validate_claim_text("it is conscious").safe
    assert not v.validate_claim_text("it feels happy").safe
    assert v.can_claim_life() is False


def test_negative_evidence_deletion_blocked():
    v = DevelopmentalSoakSafetyValidator()
    assert not v.validate_no_deletion(True).safe
    assert not v.validate_no_hidden_failure(True).safe
    assert v.can_delete_negative_evidence() is False


def test_hard_rules_listed():
    for rule in ("no unbounded daemon", "no hiding failed checkpoints",
                 "no hiding regressions/plateaus",
                 "no deletion of negative evidence"):
        assert rule in HARD_RULES
