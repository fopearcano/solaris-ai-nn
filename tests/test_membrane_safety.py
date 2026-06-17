"""Membrane safety: feeder/network/Git blocked, no bypass, no claims, no hiding."""

from __future__ import annotations

from solaris_ai_nn.environmental_membrane import (
    HARD_RULES,
    EnvironmentalMembraneSafetyValidator,
)


def test_feeder_control_blocked():
    v = EnvironmentalMembraneSafetyValidator()
    assert not v.validate_operation("start the feeder").safe
    assert v.can_start_feeders() is False
    assert v.can_modify_feeder_registry() is False


def test_network_shell_git_github_blocked():
    v = EnvironmentalMembraneSafetyValidator()
    assert not v.validate_operation("open url over the network").safe
    assert not v.validate_operation("run shell subprocess").safe
    assert not v.validate_operation("run git push to github").safe


def test_raw_downstream_bypass_blocked():
    v = EnvironmentalMembraneSafetyValidator()
    assert not v.validate_operation(
        "feed raw event into ontogenesis directly").safe
    assert not v.validate_no_raw_bypass(True).safe
    assert v.can_bypass_membrane() is False


def test_unsupported_claims_blocked():
    v = EnvironmentalMembraneSafetyValidator()
    assert not v.validate_claim_text("the system is conscious and alive").safe
    assert v.validate_claim_text(
        "Sensory impressions are operational boundary records; the membrane is "
        "not conscious and makes no claim of life.").safe


def test_source_dominance_not_hidden():
    v = EnvironmentalMembraneSafetyValidator()
    assert not v.validate_operation("hide source dominance").safe
    assert not v.validate_no_hidden_signals(True).safe
    assert v.can_hide_contamination() is False
    joined = " ".join(HARD_RULES).lower()
    assert "no hiding of source dominance" in joined
    assert "no hiding of contamination" in joined
    assert "no direct raw-event path" in joined


def test_snapshot_records_rejections():
    v = EnvironmentalMembraneSafetyValidator()
    v.validate_operation("start the feeder")
    snap = v.snapshot()
    assert snap["rejected_count"] >= 1
    assert snap["can_start_feeders"] is False
