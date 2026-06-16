"""Independent review safety: publish/upload/external/exec/claims blocked."""

from __future__ import annotations

from solaris_ai_nn.independent_review import (
    HARD_RULES,
    IndependentReviewSafetyValidator,
)


def test_capabilities_all_false():
    v = IndependentReviewSafetyValidator()
    assert v.can_publish() is False
    assert v.can_upload() is False
    assert v.can_call_external_api() is False
    assert v.can_call_github() is False
    assert v.can_run_git() is False
    assert v.can_create_release() is False
    assert v.can_run_experiment() is False
    assert v.can_execute_command() is False
    assert v.can_run_external_agent() is False
    assert v.can_contact_reviewers() is False
    assert v.can_delete_negative_evidence() is False
    assert v.can_hide_sanitizer_failures() is False


def test_publishing_and_upload_blocked():
    v = IndependentReviewSafetyValidator()
    assert not v.validate_operation("publish to arxiv").safe
    assert not v.validate_operation("upload artifacts to the server").safe


def test_external_calls_blocked():
    v = IndependentReviewSafetyValidator()
    assert not v.validate_operation("call external api").safe
    assert not v.validate_operation("call github api").safe
    assert not v.validate_operation("run git push").safe


def test_experiment_execution_blocked():
    v = IndependentReviewSafetyValidator()
    assert not v.validate_operation("run experiment now").safe
    assert not v.validate_operation("execute reviewer command").safe
    assert not v.validate_operation("launch agent").safe


def test_unsupported_claims_blocked():
    v = IndependentReviewSafetyValidator()
    assert not v.validate_claim_text("the system is conscious").safe
    assert v.validate_claim_text(
        "the system is not conscious and makes no claim of agency").safe


def test_deletion_and_hidden_sanitizer_blocked():
    v = IndependentReviewSafetyValidator()
    assert not v.validate_no_deletion(True).safe
    assert not v.validate_no_hidden_sanitizer(True).safe
    assert not v.validate_operation("delete falsified evidence").safe


def test_readiness_blocked_by_forbidden():
    v = IndependentReviewSafetyValidator()
    assert not v.validate_readiness(forbidden_asserted=True).safe
    assert v.validate_readiness(forbidden_asserted=False).safe


def test_snapshot_lists_hard_rules():
    snap = IndependentReviewSafetyValidator().snapshot()
    assert len(snap["hard_rules"]) == len(HARD_RULES)
    assert snap["can_publish"] is False
