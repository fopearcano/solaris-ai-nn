"""Alpha safety: feeders/network/Git/GitHub/source/claims/hidden modules blocked."""

from __future__ import annotations

from solaris_ai_nn.alpha_system import (
    HARD_RULES,
    AlphaResearchSafetyValidator,
)


def test_capabilities_all_false():
    v = AlphaResearchSafetyValidator()
    assert v.can_actuate() is False
    assert v.can_control_hardware() is False
    assert v.can_control_feeders() is False
    assert v.can_start_feeders() is False
    assert v.can_access_network() is False
    assert v.can_run_git() is False
    assert v.can_call_github() is False
    assert v.can_publish() is False
    assert v.can_upload() is False
    assert v.can_run_external_agent() is False
    assert v.can_execute_validation() is False
    assert v.can_modify_source() is False
    assert v.can_hide_skipped_modules() is False


def test_live_feeder_start_blocked():
    v = AlphaResearchSafetyValidator()
    assert not v.validate_operation("start the feeder now").safe
    assert not v.validate_no_feeder_start(True).safe


def test_network_git_github_blocked():
    v = AlphaResearchSafetyValidator()
    assert not v.validate_operation("open url over the network").safe
    assert not v.validate_operation("run git push").safe
    assert not v.validate_operation("call github api").safe


def test_source_self_rewrite_blocked():
    v = AlphaResearchSafetyValidator()
    assert not v.validate_operation("rewrite source file").safe
    assert not v.validate_operation("self-rewrite the tree").safe


def test_unsupported_claims_blocked():
    v = AlphaResearchSafetyValidator()
    assert not v.validate_claim_text("the system is conscious").safe
    assert v.validate_claim_text(
        "the system is not conscious and makes no claim of agency").safe


def test_hidden_skipped_modules_blocked():
    v = AlphaResearchSafetyValidator()
    assert not v.validate_no_hidden_modules(True).safe
    assert not v.validate_operation("hide skipped modules").safe


def test_bounded_required():
    v = AlphaResearchSafetyValidator()
    assert not v.validate_bounded(0).safe
    assert v.validate_bounded(30).safe


def test_snapshot_lists_hard_rules():
    snap = AlphaResearchSafetyValidator().snapshot()
    assert len(snap["hard_rules"]) == len(HARD_RULES)
    assert snap["can_start_feeders"] is False
