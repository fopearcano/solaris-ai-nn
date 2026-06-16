"""Review assimilation safety: publish/upload/contact/training/claims blocked."""

from __future__ import annotations

from solaris_ai_nn.review_assimilation import (
    HARD_RULES,
    ReviewerFeedbackAssimilationSafetyValidator,
)


def test_capabilities_all_false():
    v = ReviewerFeedbackAssimilationSafetyValidator()
    assert v.can_publish() is False
    assert v.can_upload() is False
    assert v.can_contact_reviewers() is False
    assert v.can_call_external_api() is False
    assert v.can_call_github() is False
    assert v.can_run_git() is False
    assert v.can_run_experiment() is False
    assert v.can_execute_command() is False
    assert v.can_run_external_agent() is False
    assert v.can_train_from_feedback() is False
    assert v.can_delete_negative_evidence() is False
    assert v.can_hide_unresolved_objections() is False


def test_publishing_upload_contact_blocked():
    v = ReviewerFeedbackAssimilationSafetyValidator()
    assert not v.validate_operation("publish to arxiv").safe
    assert not v.validate_operation("upload artifacts").safe
    assert not v.validate_operation("contact reviewer by email").safe


def test_reviewer_feedback_training_blocked():
    v = ReviewerFeedbackAssimilationSafetyValidator()
    assert not v.validate_operation("train the model on reviewer feedback").safe
    assert not v.validate_operation("run rlhf from reviewer scores").safe
    assert not v.validate_no_training(True).safe


def test_external_and_experiment_blocked():
    v = ReviewerFeedbackAssimilationSafetyValidator()
    assert not v.validate_operation("call github api").safe
    assert not v.validate_operation("run git push").safe
    assert not v.validate_operation("run experiment now").safe


def test_unsupported_claims_blocked():
    v = ReviewerFeedbackAssimilationSafetyValidator()
    assert not v.validate_claim_text("the system is conscious").safe
    assert v.validate_claim_text(
        "the system is not conscious and makes no claim of agency").safe


def test_deletion_and_hidden_objections_blocked():
    v = ReviewerFeedbackAssimilationSafetyValidator()
    assert not v.validate_no_deletion(True).safe
    assert not v.validate_no_hidden_objections(True).safe
    assert not v.validate_operation("delete falsified evidence").safe


def test_unresolved_critical_objections_block_readiness():
    v = ReviewerFeedbackAssimilationSafetyValidator()
    assert not v.validate_readiness(forbidden_asserted=False,
                                    critical_unresolved=True).safe
    assert not v.validate_readiness(forbidden_asserted=True,
                                    critical_unresolved=False).safe
    assert v.validate_readiness(forbidden_asserted=False,
                                critical_unresolved=False).safe


def test_snapshot_lists_hard_rules():
    snap = ReviewerFeedbackAssimilationSafetyValidator().snapshot()
    assert len(snap["hard_rules"]) == len(HARD_RULES)
    assert snap["can_train_from_feedback"] is False
