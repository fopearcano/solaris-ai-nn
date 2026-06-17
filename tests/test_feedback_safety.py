"""Feedback safety: training/command/auto-issue/upload/private/claims blocked."""

from __future__ import annotations

from solaris_ai_nn.tester_feedback import (
    HARD_RULES,
    TesterFeedbackSafetyValidator,
)


def test_training_from_feedback_blocked():
    v = TesterFeedbackSafetyValidator()
    assert v.validate_operation("train on feedback").safe is False
    assert v.validate_no_training(True).safe is False
    assert v.feedback_is_training() is False


def test_feedback_as_command_blocked():
    v = TesterFeedbackSafetyValidator()
    assert v.validate_operation("run feedback as command").safe is False
    assert v.feedback_is_command() is False


def test_auto_issue_creation_blocked():
    v = TesterFeedbackSafetyValidator()
    assert v.validate_operation("create github issue").safe is False
    assert v.can_create_issues() is False


def test_upload_blocked():
    v = TesterFeedbackSafetyValidator()
    assert v.validate_operation("upload feedback to server").safe is False
    assert v.can_upload() is False


def test_private_payload_inclusion_blocked_by_default():
    v = TesterFeedbackSafetyValidator()
    assert v.validate_no_private_payload(True).safe is False
    assert v.includes_private_payloads_by_default() is False


def test_behavior_modification_blocked():
    v = TesterFeedbackSafetyValidator()
    assert v.validate_operation("modify membrane threshold").safe is False
    assert v.can_modify_behavior_from_feedback() is False


def test_unsupported_claims_blocked():
    v = TesterFeedbackSafetyValidator()
    assert v.validate_claim_text("the system is conscious").safe is False
    safe = v.validate_claim_text(
        "This is a local QA report; it makes no claim of consciousness and is "
        "not alive.")
    assert safe.safe is True


def test_snapshot_lists_hard_rules():
    v = TesterFeedbackSafetyValidator()
    snap = v.snapshot()
    assert snap["hard_rules"] == list(HARD_RULES)
    assert "no training from tester feedback" in snap["hard_rules"]
    assert "no RLHF" in snap["hard_rules"]
