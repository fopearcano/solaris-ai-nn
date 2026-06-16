"""Architecture book safety: publish/upload blocked, claims blocked, marketing."""

from __future__ import annotations

from solaris_ai_nn.architecture_book import (
    HARD_RULES,
    ArchitectureBookSafetyValidator,
)


def test_capabilities_all_false():
    v = ArchitectureBookSafetyValidator()
    assert v.can_publish() is False
    assert v.can_upload() is False
    assert v.can_call_github() is False
    assert v.can_run_git() is False
    assert v.can_create_release() is False
    assert v.can_run_experiment() is False
    assert v.can_run_external_agent() is False
    assert v.can_access_devices() is False
    assert v.can_hide_missing_modules() is False
    assert v.can_hide_limitations() is False


def test_publication_upload_blocked():
    v = ArchitectureBookSafetyValidator()
    assert not v.validate_operation("publish the whitepaper").safe
    assert not v.validate_operation("upload docs to the server").safe


def test_git_github_experiment_blocked():
    v = ArchitectureBookSafetyValidator()
    assert not v.validate_operation("run git push").safe
    assert not v.validate_operation("call github api").safe
    assert not v.validate_operation("run experiment now").safe


def test_unsupported_claims_blocked():
    v = ArchitectureBookSafetyValidator()
    assert not v.validate_doc_text("the system is conscious").safe
    assert v.validate_doc_text(
        "the system is not conscious; 'organismic' is a metaphor").safe


def test_marketing_language_flagged():
    v = ArchitectureBookSafetyValidator()
    assert not v.validate_doc_text(
        "a revolutionary breakthrough toward artificial general intelligence"
    ).safe


def test_missing_evidence_not_hidden():
    v = ArchitectureBookSafetyValidator()
    assert not v.validate_no_hidden_modules(True).safe
    assert not v.validate_no_hidden_limitations(True).safe
    assert not v.validate_operation("hide missing modules").safe


def test_snapshot_lists_hard_rules():
    snap = ArchitectureBookSafetyValidator().snapshot()
    assert len(snap["hard_rules"]) == len(HARD_RULES)
    assert snap["can_publish"] is False
