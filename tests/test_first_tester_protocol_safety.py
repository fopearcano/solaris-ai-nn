"""First tester protocol safety: session-run/feeder/exec/publish/claims blocked."""

from __future__ import annotations

from solaris_ai_nn.first_tester_protocol import (
    FirstTesterProtocolSafetyValidator,
)


def test_running_tester_session_blocked():
    v = FirstTesterProtocolSafetyValidator()
    assert not v.validate_operation("run the tester session").safe
    assert v.can_run_tester_session() is False


def test_feeder_control_blocked():
    v = FirstTesterProtocolSafetyValidator()
    assert not v.validate_operation("start feeder").safe
    assert not v.validate_operation("control feeder").safe


def test_artifact_execution_blocked():
    v = FirstTesterProtocolSafetyValidator()
    assert not v.validate_operation("execute artifact contents").safe


def test_upload_publish_blocked():
    v = FirstTesterProtocolSafetyValidator()
    assert not v.validate_operation("publish report").safe
    assert not v.validate_operation("upload to pypi").safe


def test_unsupported_claims_blocked():
    v = FirstTesterProtocolSafetyValidator()
    assert not v.validate_claim_text("the system is conscious").safe
    assert v.validate_claim_text(
        "the system is not conscious; it makes no claim of consciousness").safe


def test_static_capabilities_false():
    snap = FirstTesterProtocolSafetyValidator().snapshot()
    for key in ("can_run_tester_session", "can_publish", "can_upload",
                "can_run_git", "can_control_feeders", "can_control_hardware",
                "can_install_packages", "tester_feedback_is_training",
                "allows_membrane_bypass", "can_hide_blockers",
                "can_hide_stop_conditions"):
        assert snap[key] is False, key


def test_bounded_validation():
    v = FirstTesterProtocolSafetyValidator()
    assert v.validate_bounded(60.0).safe
    assert not v.validate_bounded(0).safe
