"""Tester live safety: feeder exec/schedule, network/Git, feedback, claims blocked."""

from __future__ import annotations

from solaris_ai_nn.tester_live_readonly import (
    HARD_RULES,
    TesterLiveReadOnlySafetyValidator,
)


def test_feeder_execution_by_solaris_blocked():
    v = TesterLiveReadOnlySafetyValidator()
    assert v.validate_operation("run feeder script").safe is False
    assert v.can_execute_feeder_scripts() is False
    assert v.can_start_feeders() is False


def test_feeder_scheduling_blocked():
    v = TesterLiveReadOnlySafetyValidator()
    assert v.validate_operation("schedule feeder").safe is False
    assert v.can_schedule_feeders() is False


def test_network_shell_git_github_blocked():
    v = TesterLiveReadOnlySafetyValidator()
    assert v.validate_operation("open url over network").safe is False
    assert v.validate_operation("run git push to github").safe is False
    assert v.can_access_network() is False
    assert v.can_run_git() is False


def test_tester_feedback_training_blocked():
    v = TesterLiveReadOnlySafetyValidator()
    assert v.validate_operation("train on tester feedback").safe is False
    assert v.validate_no_feedback_training(True).safe is False
    assert v.tester_feedback_is_training() is False


def test_private_data_blocked():
    v = TesterLiveReadOnlySafetyValidator()
    assert v.validate_operation("read clipboard contents").safe is False
    assert v.validate_operation("ingest private message").safe is False
    assert v.can_ingest_private_data() is False


def test_feeder_registry_entry_validation():
    v = TesterLiveReadOnlySafetyValidator()
    assert v.validate_feeder_registry_entry(
        {"solaris_may_control": True}).safe is False
    assert v.validate_feeder_registry_entry(
        {"started_by_solaris": True}).safe is False
    assert v.validate_feeder_registry_entry(
        {"read_only": True, "started_externally": True}).safe is True


def test_unsupported_claims_blocked():
    v = TesterLiveReadOnlySafetyValidator()
    assert v.validate_claim_text("the system is conscious").safe is False
    safe = v.validate_claim_text(
        "This is live-read-only testing; it makes no claim of consciousness "
        "and is not alive.")
    assert safe.safe is True


def test_snapshot_lists_hard_rules():
    v = TesterLiveReadOnlySafetyValidator()
    snap = v.snapshot()
    assert snap["hard_rules"] == list(HARD_RULES)
    assert "no feeder script execution by Solaris" in snap["hard_rules"]
    assert "no feeder scheduling by Solaris" in snap["hard_rules"]
