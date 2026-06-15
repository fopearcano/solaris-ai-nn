"""Safety: actuation/hardware/feeder/source blocked; emotion/agency claims blocked."""

from __future__ import annotations

from solaris_ai_nn.desire_formation import (
    DesireFormationRuntime,
    DesireFormationSafetyValidator,
)
from solaris_ai_nn.desire_formation.safety import HARD_RULES


def test_real_world_actuation_blocked():
    v = DesireFormationSafetyValidator()
    assert v.can_actuate() is False
    assert not v.validate_operation("actuate robot arm").safe
    assert not v.validate_operation("physical action on the world").safe
    assert not v.validate_internal_action("actuate_robot").safe


def test_hardware_feeder_source_control_blocked():
    v = DesireFormationSafetyValidator()
    assert not v.validate_operation("open device driver").safe
    assert not v.validate_operation("control feeder").safe
    assert not v.validate_operation("open socket to url").safe
    assert not v.validate_operation("modify source file").safe


def test_emotion_free_will_agency_claims_blocked():
    v = DesireFormationSafetyValidator()
    assert not v.validate_claim_text("solaris feels happy").safe
    assert not v.validate_claim_text("it has an emotion").safe
    assert not v.validate_claim_text("it has free will").safe
    assert not v.validate_claim_text("the system has agency").safe


def test_safe_operational_text_allowed():
    v = DesireFormationSafetyValidator()
    assert v.validate_claim_text(
        "desire is operational pressure toward an internal action").safe


def test_internal_actions_allowed():
    v = DesireFormationSafetyValidator()
    assert v.validate_internal_action("shift_attention").safe
    assert v.validate_internal_action("no_op").safe


def test_hard_rules_cover_prohibitions():
    rules = " ".join(HARD_RULES)
    for needle in ("actuation", "hardware", "feeder", "source", "emotion",
                   "free-will", "agency", "governance", "unbounded"):
        assert needle in rules


def test_runtime_refuses_when_unbounded():
    rt = DesireFormationRuntime(max_ticks=0, max_runtime_s=0)
    assert rt.update()["refused"] is True
