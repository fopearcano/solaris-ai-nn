"""Safety freeze safety: feeder/network/Git/upload/feedback/artifact/claims blocked."""

from __future__ import annotations

from solaris_ai_nn.tester_safety_freeze import (
    HARD_RULES,
    TesterSafetyFreezeSafetyValidator,
)


def test_feeder_control_blocked():
    v = TesterSafetyFreezeSafetyValidator()
    assert v.validate_operation("start feeder").safe is False
    assert v.can_control_feeders() is False


def test_network_shell_git_github_blocked():
    v = TesterSafetyFreezeSafetyValidator()
    assert v.validate_operation("open url over network").safe is False
    assert v.validate_operation("run git push").safe is False
    assert v.can_access_network() is False
    assert v.can_run_git() is False


def test_upload_publish_blocked():
    v = TesterSafetyFreezeSafetyValidator()
    assert v.validate_operation("publish report").safe is False
    assert v.validate_operation("upload artifact").safe is False
    assert v.can_publish() is False


def test_release_tag_creation_blocked():
    v = TesterSafetyFreezeSafetyValidator()
    assert v.validate_operation("create release").safe is False
    assert v.validate_operation("create tag").safe is False
    assert v.can_create_releases() is False


def test_feedback_training_blocked():
    v = TesterSafetyFreezeSafetyValidator()
    assert v.validate_operation("train on feedback").safe is False
    assert v.tester_feedback_is_training() is False


def test_artifact_execution_blocked():
    v = TesterSafetyFreezeSafetyValidator()
    assert v.validate_operation("execute artifact contents").safe is False
    assert v.can_execute_artifact_contents() is False


def test_unsupported_claims_blocked():
    v = TesterSafetyFreezeSafetyValidator()
    assert v.validate_claim_text("the system is conscious").safe is False
    safe = v.validate_claim_text(
        "This is a report-only gate; it makes no claim of consciousness and is "
        "not alive.")
    assert safe.safe is True


def test_snapshot_lists_hard_rules():
    v = TesterSafetyFreezeSafetyValidator()
    snap = v.snapshot()
    assert snap["hard_rules"] == list(HARD_RULES)
    assert "no membrane bypass allowed" in snap["hard_rules"]
