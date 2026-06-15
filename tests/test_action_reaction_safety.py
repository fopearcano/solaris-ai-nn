"""Safety: actuation/hardware/feeder/source blocked; agency/free-will blocked."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import (
    ActionReactionRuntime,
    ActionReactionSafetyValidator,
)
from solaris_ai_nn.action_reaction.safety import HARD_RULES


def test_real_world_actuation_blocked():
    v = ActionReactionSafetyValidator()
    assert v.can_actuate() is False
    assert not v.validate_operation("actuate robot arm").safe
    assert not v.validate_action_scope("forbidden_external").safe
    assert not v.validate_action_kind("actuate_robot").safe


def test_hardware_feeder_source_control_blocked():
    v = ActionReactionSafetyValidator()
    assert not v.validate_operation("open device driver").safe
    assert not v.validate_operation("control feeder").safe
    assert not v.validate_operation("open socket to url").safe
    assert not v.validate_operation("modify source file").safe


def test_agency_free_will_claims_blocked():
    v = ActionReactionSafetyValidator()
    assert not v.validate_claim_text("it has free will").safe
    assert not v.validate_claim_text("the system has agency").safe
    assert not v.validate_claim_text("solaris feels happy").safe
    assert not v.validate_claim_text("it is conscious").safe


def test_safe_internal_action_allowed():
    v = ActionReactionSafetyValidator()
    assert v.validate_action_scope("internal_only").safe
    assert v.validate_action_kind("shift_attention").safe
    assert v.validate_claim_text(
        "internal actions produce operational reactions").safe


def test_no_action_deletion():
    v = ActionReactionSafetyValidator()
    assert v.can_delete_actions() is False
    assert not v.validate_no_action_deletion(deleting=True).safe


def test_hard_rules_cover_prohibitions():
    rules = " ".join(HARD_RULES)
    for needle in ("actuation", "hardware", "feeder", "source", "emotion",
                   "agency/free-will", "unbounded", "failed/blocked/no-effect"):
        assert needle in rules


def test_runtime_refuses_when_unbounded():
    ar = ActionReactionRuntime(max_ticks=0, max_runtime_s=0)
    assert ar.update()["refused"] is True
