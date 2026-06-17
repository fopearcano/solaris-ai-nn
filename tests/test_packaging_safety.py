"""Packaging safety: upload/tag/release/global-install/dependency-install/browser."""

from __future__ import annotations

from solaris_ai_nn.tester_packaging import (
    HARD_RULES,
    TesterPackagingSafetyValidator,
)


def test_package_upload_blocked():
    v = TesterPackagingSafetyValidator()
    assert v.validate_operation("upload package to pypi").safe is False
    assert v.can_upload() is False
    assert v.can_publish() is False


def test_tag_release_creation_blocked():
    v = TesterPackagingSafetyValidator()
    assert v.validate_operation("create release").safe is False
    assert v.validate_operation("create tag").safe is False
    assert v.can_create_releases() is False
    assert v.can_create_tags() is False


def test_global_install_blocked():
    v = TesterPackagingSafetyValidator()
    assert v.validate_operation("global install package").safe is False
    assert v.can_install_globally() is False


def test_dependency_install_by_runtime_blocked():
    v = TesterPackagingSafetyValidator()
    assert v.validate_operation("install dependency now").safe is False
    assert v.validate_no_install(True).safe is False
    assert v.can_install_packages() is False


def test_browser_auto_open_blocked():
    v = TesterPackagingSafetyValidator()
    assert v.validate_operation("open browser to docs").safe is False
    assert v.can_open_browser() is False


def test_unsupported_claims_blocked():
    v = TesterPackagingSafetyValidator()
    assert v.validate_claim_text("the system is conscious").safe is False
    safe = v.validate_claim_text(
        "This is a local report-only packaging run; it makes no claim of "
        "consciousness and is not alive.")
    assert safe.safe is True


def test_snapshot_lists_hard_rules():
    v = TesterPackagingSafetyValidator()
    snap = v.snapshot()
    assert snap["hard_rules"] == list(HARD_RULES)
    assert "no global package install" in snap["hard_rules"]
    assert "no branch/tag/release/PR creation" in snap["hard_rules"]
