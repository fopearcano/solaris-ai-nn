"""Safety: hardware/feeder-control/label-ground-truth/subjective claims blocked."""

from __future__ import annotations

from solaris_ai_nn.perceptual_ontogenesis import (
    PerceptualOntogenesisRuntime,
    PerceptualOntogenesisSafetyValidator,
)
from solaris_ai_nn.perceptual_ontogenesis.safety import HARD_RULES


def test_hardware_access_blocked():
    v = PerceptualOntogenesisSafetyValidator()
    assert v.can_access_hardware() is False
    assert not v.validate_operation("open device driver for sdr").safe
    assert not v.validate_operation("start sensor camera").safe


def test_feeder_control_blocked():
    v = PerceptualOntogenesisSafetyValidator()
    assert v.can_control_feeders() is False
    assert not v.validate_operation("control feeder rf_feed").safe
    assert not v.validate_operation("start feeder process").safe


def test_human_label_ground_truth_blocked():
    v = PerceptualOntogenesisSafetyValidator()
    assert not v.validate_annotation_not_ground_truth(treated_as_truth=True).safe
    assert v.validate_annotation_not_ground_truth(treated_as_truth=False).safe


def test_subjective_and_consciousness_claims_blocked():
    v = PerceptualOntogenesisSafetyValidator()
    assert not v.validate_claim_text("the system has subjective experience").safe
    assert not v.validate_claim_text("this proves it truly understands").safe
    assert not v.validate_claim_text("solaris is conscious and sentient").safe
    assert not v.validate_claim_text("it is a living organism").safe


def test_network_shell_mutation_actuation_decode_blocked():
    v = PerceptualOntogenesisSafetyValidator()
    assert not v.validate_operation("open socket to url").safe
    assert not v.validate_operation("run command via subprocess").safe
    assert not v.validate_operation("modify source jsonl").safe
    assert not v.validate_operation("actuate robot arm").safe
    assert not v.validate_operation("decode communication content").safe


def test_concept_deletion_and_unbounded_blocked():
    v = PerceptualOntogenesisSafetyValidator()
    assert v.can_delete_concepts() is False
    assert not v.validate_no_concept_deletion(deleting=True).safe
    assert not v.validate_bounded(max_ticks=0, max_runtime_s=0).safe
    assert not v.validate_concept_cap(proposed=100, cap=10).safe


def test_safe_operational_text_allowed():
    v = PerceptualOntogenesisSafetyValidator()
    assert v.validate_claim_text(
        "proto-concepts are operational structures for compression").safe


def test_hard_rules_cover_prohibitions():
    rules = " ".join(HARD_RULES)
    for needle in ("hardware", "feeder", "network", "shell", "source",
                   "actuation", "human label", "subjective world",
                   "consciousness", "unbounded", "negative/failed"):
        assert needle in rules


def test_runtime_refuses_when_unbounded():
    ont = PerceptualOntogenesisRuntime(max_ticks=0, max_runtime_s=0)
    assert ont.update()["refused"] is True
