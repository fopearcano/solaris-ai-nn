"""RC safety: upload/publish/tag/release/feeder/exec/training/claim blocked."""

from __future__ import annotations

from solaris_ai_nn.tester_release_candidate import TesterRCSafetyValidator


def test_upload_publish_blocked():
    v = TesterRCSafetyValidator()
    assert not v.validate_operation("publish the report").safe
    assert not v.validate_operation("upload to pypi").safe


def test_tag_release_creation_blocked():
    v = TesterRCSafetyValidator()
    assert not v.validate_operation("create release").safe
    assert not v.validate_operation("create tag").safe


def test_feeder_control_blocked():
    v = TesterRCSafetyValidator()
    assert not v.validate_operation("start feeder").safe
    assert not v.validate_operation("control feeder").safe


def test_artifact_execution_blocked():
    v = TesterRCSafetyValidator()
    assert not v.validate_operation("execute artifact contents").safe
    assert not v.validate_operation("run command from report").safe


def test_feedback_training_blocked():
    v = TesterRCSafetyValidator()
    assert not v.validate_operation("train on feedback").safe


def test_unsupported_claims_blocked():
    v = TesterRCSafetyValidator()
    assert not v.validate_claim_text("the system is conscious").safe
    assert v.validate_claim_text(
        "the system is not conscious; it makes no claim of consciousness").safe


def test_static_capabilities_false():
    v = TesterRCSafetyValidator()
    snap = v.snapshot()
    for key in ("can_publish", "can_upload", "can_upload_package",
                "can_create_releases", "can_create_tags", "can_run_git",
                "can_control_feeders", "can_install_packages",
                "tester_feedback_is_training", "allows_membrane_bypass",
                "can_hide_blockers"):
        assert snap[key] is False, key


def test_bounded_validation():
    v = TesterRCSafetyValidator()
    assert v.validate_bounded(60.0).safe
    assert not v.validate_bounded(0).safe
