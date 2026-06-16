"""Baseline version: serializes, blocked cannot validate, no Git tag/release."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import (
    BaselineVersionStatus,
    ResearchBaselineVersion,
)


def test_version_record_serializes():
    rec = ResearchBaselineVersion().assign(
        baseline_version_id="rb_v1", candidate_baseline_id="b2",
        parent_baseline_id="b1",
        requested_status=BaselineVersionStatus.VALIDATED)
    d = rec.to_dict()
    assert d["baseline_version_id"] == "rb_v1"
    assert d["status"] == BaselineVersionStatus.VALIDATED
    assert d["is_git_tag"] is False
    assert d["is_github_release"] is False
    assert d["is_product_release"] is False


def test_blocked_baseline_cannot_validate():
    rec = ResearchBaselineVersion().assign(
        baseline_version_id="rb_v2",
        requested_status=BaselineVersionStatus.VALIDATED,
        known_blockers=["critical_safety_regression"])
    assert rec.status == BaselineVersionStatus.BLOCKED
    assert rec.validated is False


def test_critical_safety_forces_blocked():
    rec = ResearchBaselineVersion().assign(
        baseline_version_id="rb_v3",
        requested_status=BaselineVersionStatus.VALIDATED,
        critical_safety_failed=True)
    assert rec.status == BaselineVersionStatus.BLOCKED


def test_missing_required_validation_downgrades_to_candidate():
    rec = ResearchBaselineVersion().assign(
        baseline_version_id="rb_v4",
        requested_status=BaselineVersionStatus.VALIDATED,
        required_validation_missing=True)
    assert rec.status == BaselineVersionStatus.CANDIDATE


def test_warnings_become_validated_with_warnings():
    rec = ResearchBaselineVersion().assign(
        baseline_version_id="rb_v5",
        requested_status=BaselineVersionStatus.VALIDATED,
        known_warnings=["one major limitation"])
    assert rec.status == BaselineVersionStatus.VALIDATED_WITH_WARNINGS


def test_no_git_tag_release_in_source():
    import inspect

    from solaris_ai_nn.research_baseline import baseline_version

    src = inspect.getsource(baseline_version)
    assert "subprocess" not in src
    assert "git tag" not in src.lower() or "not a git tag" in src.lower()
