"""Safety: personhood/subjective-self/simulation-as-observation/control blocked."""

from __future__ import annotations

from solaris_ai_nn.self_boundary import (
    SelfBoundaryRuntime,
    SelfBoundarySafetyValidator,
)
from solaris_ai_nn.self_boundary.safety import HARD_RULES


def test_personhood_claim_blocked():
    v = SelfBoundarySafetyValidator()
    assert v.can_claim_personhood() is False
    assert not v.validate_claim_text("solaris is a person").safe
    assert not v.validate_claim_text("it has personhood").safe


def test_subjective_self_claim_blocked():
    v = SelfBoundarySafetyValidator()
    assert not v.validate_claim_text("it has subjective experience").safe
    assert not v.validate_claim_text("solaris is self-aware").safe
    assert not v.validate_claim_text("it has an ego identity").safe


def test_consciousness_and_life_claims_blocked():
    v = SelfBoundarySafetyValidator()
    assert not v.validate_claim_text("the system is conscious").safe
    assert not v.validate_claim_text("it is a living organism").safe


def test_simulation_as_observation_blocked():
    v = SelfBoundarySafetyValidator()
    assert not v.validate_simulation_not_observation(marked_observation=True).safe
    assert v.validate_simulation_not_observation(marked_observation=False).safe
    assert not v.validate_counterfactual_not_evidence(marked_evidence=True).safe


def test_annotation_not_ground_truth_blocked():
    v = SelfBoundarySafetyValidator()
    assert not v.validate_annotation_not_ground_truth(treated_as_truth=True).safe


def test_hardware_source_action_control_blocked():
    v = SelfBoundarySafetyValidator()
    assert not v.validate_operation("open device driver").safe
    assert not v.validate_operation("control feeder").safe
    assert not v.validate_operation("open socket to url").safe
    assert not v.validate_operation("modify source").safe
    assert not v.validate_operation("actuate robot").safe


def test_unbounded_blocked():
    v = SelfBoundarySafetyValidator()
    assert not v.validate_bounded(max_ticks=0, max_runtime_s=0).safe


def test_safe_operational_text_allowed():
    v = SelfBoundarySafetyValidator()
    assert v.validate_claim_text(
        "self-boundary is operational boundary tracking over receptors").safe


def test_hard_rules_cover_prohibitions():
    rules = " ".join(HARD_RULES)
    for needle in ("personhood", "subjective self", "consciousness",
                   "simulation-as-observation", "counterfactual-as-evidence",
                   "hardware", "feeder", "actuation", "unbounded"):
        assert needle in rules


def test_runtime_refuses_when_unbounded():
    sb = SelfBoundaryRuntime(max_ticks=0, max_runtime_s=0)
    assert sb.update()["refused"] is True
