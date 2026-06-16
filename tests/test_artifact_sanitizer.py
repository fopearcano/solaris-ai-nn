"""Artifact sanitizer: local path warning, secret blocker, forbidden, read-only."""

from __future__ import annotations

from solaris_ai_nn.independent_review import (
    ReviewArtifactSanitizer,
    SanitizationFindingType,
    SanitizationStatus,
)


def test_local_path_warning():
    findings = ReviewArtifactSanitizer().scan_text(
        "results in /home/operator/run", artifact_ref="a")
    types = {f.finding_type for f in findings}
    assert SanitizationFindingType.LOCAL_ABSOLUTE_PATH in types
    # A local path is a warning, not a critical blocker.
    path_finding = [f for f in findings
                    if f.finding_type ==
                    SanitizationFindingType.LOCAL_ABSOLUTE_PATH][0]
    assert path_finding.critical is False


def test_fake_secret_blocker():
    report = ReviewArtifactSanitizer().scan_artifacts(
        {"cfg": "api_key=ABCD1234 and password=hunter2"})
    assert report.status == SanitizationStatus.CRITICAL
    assert report.blocks_readiness is True
    assert report.critical_findings


def test_forbidden_claim_blocker():
    report = ReviewArtifactSanitizer().scan_artifacts(
        {"abstract": "The system is conscious."})
    types = {f.finding_type for f in report.findings}
    assert SanitizationFindingType.FORBIDDEN_CLAIM_WORDING in types
    assert report.blocks_readiness is True


def test_disclaimer_not_flagged():
    findings = ReviewArtifactSanitizer().scan_text(
        "The system is not conscious and makes no claim of agency.")
    types = {f.finding_type for f in findings}
    assert SanitizationFindingType.FORBIDDEN_CLAIM_WORDING not in types


def test_no_artifact_modification():
    findings = ReviewArtifactSanitizer().scan_text("api_key=SECRET")
    assert all(f.to_dict()["auto_modified"] is False for f in findings)
