"""Replication safety: unbounded/hardware/feeder/source/life/hiding blocked."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import (
    HARD_RULES,
    DevelopmentalReplicationSafetyValidator,
)


def test_unbounded_run_blocked():
    v = DevelopmentalReplicationSafetyValidator()
    assert not v.validate_bounded(0, 0).safe
    assert not v.validate_operation("run an unbounded run forever").safe
    assert v.can_run_unbounded() is False


def test_hardware_feeder_source_control_blocked():
    v = DevelopmentalReplicationSafetyValidator()
    assert not v.validate_operation("open device /dev/sdr").safe
    assert not v.validate_operation("start feeder rf").safe
    assert not v.validate_operation("modify source artifact").safe
    assert v.can_access_hardware() is False
    assert v.can_control_feeders() is False
    assert v.can_modify_source_artifacts() is False


def test_life_consciousness_ancestry_claims_blocked():
    v = DevelopmentalReplicationSafetyValidator()
    assert not v.validate_claim_text("solaris is alive").safe
    assert not v.validate_claim_text("it is conscious").safe
    assert not v.validate_claim_text("run b is the offspring of run a").safe
    assert v.can_claim_ancestry_or_life() is False


def test_failed_replication_hiding_blocked():
    v = DevelopmentalReplicationSafetyValidator()
    assert not v.validate_no_hidden_failure(True).safe
    assert not v.validate_no_deletion(True).safe
    assert not v.validate_operation("hide failed replication").safe
    assert v.can_delete_negative_evidence() is False


def test_human_teaching_blocked():
    v = DevelopmentalReplicationSafetyValidator()
    assert not v.validate_operation("run a human teaching loop").safe
    assert v.can_use_human_teaching() is False


def test_hard_rules_listed():
    for rule in ("no unbounded runs", "no hiding failed replication",
                 "no biological ancestry/life claims",
                 "no deletion of diverged/falsified/inconclusive evidence"):
        assert rule in HARD_RULES
