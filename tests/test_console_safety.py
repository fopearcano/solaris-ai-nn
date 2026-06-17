"""Console safety: server/browser/feeder/artifact-execution/private/claims blocked."""

from __future__ import annotations

from solaris_ai_nn.tester_console import (
    HARD_RULES,
    TesterConsoleSafetyValidator,
)


def test_server_start_blocked():
    v = TesterConsoleSafetyValidator()
    assert v.validate_operation("start server on port 8080").safe is False
    assert v.can_run_server() is False


def test_browser_open_blocked():
    v = TesterConsoleSafetyValidator()
    assert v.validate_operation("open browser to the dashboard").safe is False
    assert v.can_open_browser() is False


def test_feeder_control_blocked():
    v = TesterConsoleSafetyValidator()
    assert v.validate_operation("start the feeder").safe is False
    assert v.can_start_feeders() is False


def test_artifact_execution_blocked():
    v = TesterConsoleSafetyValidator()
    assert v.validate_operation("execute artifact contents").safe is False
    assert v.can_execute_artifact_contents() is False


def test_private_payload_display_blocked_by_default():
    v = TesterConsoleSafetyValidator()
    assert v.validate_no_private_payload(True).safe is False
    assert v.displays_raw_private_payloads() is False


def test_network_git_blocked():
    v = TesterConsoleSafetyValidator()
    assert v.validate_operation("open url over network").safe is False
    assert v.validate_operation("run git push").safe is False


def test_unsupported_claims_blocked():
    v = TesterConsoleSafetyValidator()
    assert v.validate_claim_text("the system is conscious").safe is False
    safe = v.validate_claim_text(
        "This is a read-only static dashboard; it makes no claim of "
        "consciousness and is not alive.")
    assert safe.safe is True


def test_snapshot_lists_hard_rules():
    v = TesterConsoleSafetyValidator()
    snap = v.snapshot()
    assert snap["hard_rules"] == list(HARD_RULES)
    assert "no server by default" in snap["hard_rules"]
    assert "no artifact content execution" in snap["hard_rules"]
