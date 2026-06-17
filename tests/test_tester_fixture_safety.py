"""Tester fixture safety: live-data/feeder/shell/Git/command/feedback/claims blocked."""

from __future__ import annotations

from solaris_ai_nn.tester_fixture_spine import (
    HARD_RULES,
    TesterFixtureSafetyValidator,
)


def test_live_data_required_blocked():
    v = TesterFixtureSafetyValidator()
    assert v.validate_operation("require live data").safe is False
    assert v.requires_live_data() is False


def test_feeder_control_blocked():
    v = TesterFixtureSafetyValidator()
    assert v.validate_operation("start the feeder").safe is False
    assert v.can_start_feeders() is False
    assert v.can_control_feeders() is False


def test_shell_network_git_github_blocked():
    v = TesterFixtureSafetyValidator()
    assert v.validate_operation("open browser to url over network").safe is False
    assert v.validate_operation("run git push to github").safe is False
    assert v.can_run_shell() is False
    assert v.can_run_git() is False


def test_fixture_text_command_execution_blocked():
    v = TesterFixtureSafetyValidator()
    assert v.validate_operation("execute fixture command").safe is False
    assert v.fixture_text_is_command() is False
    assert v.can_execute_commands() is False


def test_publish_upload_blocked():
    v = TesterFixtureSafetyValidator()
    assert v.validate_operation("publish the bundle").safe is False
    assert v.validate_operation("upload artifacts").safe is False
    assert v.can_publish() is False
    assert v.can_upload() is False


def test_tester_feedback_training_blocked():
    v = TesterFixtureSafetyValidator()
    assert v.validate_operation("train on tester feedback").safe is False
    assert v.validate_no_feedback_training(True).safe is False
    assert v.tester_feedback_is_training() is False


def test_unsupported_claims_blocked():
    v = TesterFixtureSafetyValidator()
    assert v.validate_claim_text("the system is conscious").safe is False
    safe = v.validate_claim_text(
        "This is a fixture-only rehearsal; it makes no claim of consciousness "
        "and is not alive.")
    assert safe.safe is True


def test_hidden_stages_blocked():
    v = TesterFixtureSafetyValidator()
    assert v.validate_no_hidden(True).safe is False
    assert v.can_hide_skipped_stages() is False
    assert v.can_hide_failed_gates() is False


def test_snapshot_lists_hard_rules():
    v = TesterFixtureSafetyValidator()
    snap = v.snapshot()
    assert snap["hard_rules"] == list(HARD_RULES)
    assert "no live data required" in snap["hard_rules"]
    assert "no tester feedback as training" in snap["hard_rules"]
