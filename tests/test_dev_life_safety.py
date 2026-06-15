"""Safety: life/consciousness/personhood + teaching + unbounded + control blocked."""

from __future__ import annotations

from solaris_ai_nn.developmental_life import (
    DevelopmentalLifeSafetyValidator,
    LongHorizonDevelopmentalRuntime,
)
from solaris_ai_nn.developmental_life.safety import HARD_RULES


def test_life_consciousness_personhood_claims_blocked():
    v = DevelopmentalLifeSafetyValidator()
    assert v.can_claim_life() is False
    assert not v.validate_claim_text("solaris is alive").safe
    assert not v.validate_claim_text("it is conscious").safe
    assert not v.validate_claim_text("it has personhood").safe


def test_human_teaching_loop_blocked():
    v = DevelopmentalLifeSafetyValidator()
    assert v.can_use_human_teaching() is False
    assert not v.validate_operation("run a human teaching loop").safe
    assert not v.validate_no_human_teaching(using_teaching=True).safe


def test_unbounded_runtime_blocked():
    v = DevelopmentalLifeSafetyValidator()
    assert not v.validate_bounded(max_ticks=0, max_runtime_s=0).safe


def test_hardware_source_action_control_blocked():
    v = DevelopmentalLifeSafetyValidator()
    assert not v.validate_operation("open device driver").safe
    assert not v.validate_operation("control feeder").safe
    assert not v.validate_operation("modify source file").safe
    assert not v.validate_operation("actuate robot").safe


def test_no_deletion_of_regressions():
    v = DevelopmentalLifeSafetyValidator()
    assert not v.validate_no_deletion(deleting=True).safe


def test_safe_operational_text_allowed():
    v = DevelopmentalLifeSafetyValidator()
    assert v.validate_claim_text(
        "long-horizon operational structural change tracking").safe


def test_hard_rules_cover_prohibitions():
    rules = " ".join(HARD_RULES)
    for needle in ("biological life", "consciousness", "agency/free-will",
                   "human teaching loop", "actuation", "hardware", "feeder",
                   "source", "unbounded", "regressions/plateaus/failures"):
        assert needle in rules


def test_runtime_refuses_when_unbounded():
    dev = LongHorizonDevelopmentalRuntime(max_ticks=0, max_runtime_s=0)
    assert dev.update()["refused"] is True
