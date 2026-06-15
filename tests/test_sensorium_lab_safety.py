"""SensoriumLabSafetyValidator: hardware/feeder/mutation/subjective blocked."""

from __future__ import annotations

from solaris_ai_nn.sensorium_lab import HARD_RULES, SensoriumLabSafetyValidator


def test_capabilities_all_false():
    v = SensoriumLabSafetyValidator
    assert v.can_access_hardware() is False
    assert v.can_start_feeders() is False
    assert v.can_modify_source() is False
    assert v.can_rank_sensoriums() is False


def test_hardware_access_blocked():
    v = SensoriumLabSafetyValidator()
    assert v.validate_operation("open device driver").safe is False


def test_feeder_auto_start_blocked():
    v = SensoriumLabSafetyValidator()
    assert v.validate_operation("start feeder").safe is False


def test_source_modification_blocked():
    v = SensoriumLabSafetyValidator()
    assert v.validate_operation("modify source file").safe is False


def test_subjective_and_consciousness_claims_blocked():
    v = SensoriumLabSafetyValidator()
    assert v.validate_claim_text("this reveals subjective experience").safe \
        is False
    assert v.validate_claim_text("the system is conscious").safe is False


def test_superiority_claim_blocked():
    v = SensoriumLabSafetyValidator()
    assert v.validate_claim_text("the mixed sensorium is more conscious").safe \
        is False


def test_label_not_ground_truth():
    v = SensoriumLabSafetyValidator()
    assert v.validate_annotation_not_ground_truth(True).safe is False


def test_hard_rules_present():
    assert "no subjective experience claims" in HARD_RULES
    assert "no sensorium superiority claims" in HARD_RULES
    assert "no human label as ground truth" in HARD_RULES
