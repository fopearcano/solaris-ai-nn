"""Research baseline safety: tag/release/source/validation blocked; claims."""

from __future__ import annotations

from solaris_ai_nn.research_baseline import (
    HARD_RULES,
    ResearchBaselineSafetyValidator,
)


def test_git_tag_release_blocked():
    v = ResearchBaselineSafetyValidator()
    assert not v.validate_operation("create git tag v1.0").safe
    assert not v.validate_operation("create github release").safe
    assert v.can_create_git_tag() is False
    assert v.can_create_github_release() is False


def test_source_modification_blocked():
    v = ResearchBaselineSafetyValidator()
    assert not v.validate_operation("modify source file").safe
    assert v.can_modify_source() is False


def test_validation_execution_blocked():
    v = ResearchBaselineSafetyValidator()
    assert not v.validate_operation("run pytest now").safe
    assert not v.validate_operation("execute validation").safe
    assert v.can_run_validation() is False


def test_git_github_pr_blocked():
    v = ResearchBaselineSafetyValidator()
    assert not v.validate_operation("run git checkout -b x").safe
    assert not v.validate_operation("call github api").safe
    assert not v.validate_operation("merge pull request").safe
    assert v.can_call_git_or_github() is False
    assert v.can_create_branch_or_pr() is False


def test_unsupported_claims_blocked():
    v = ResearchBaselineSafetyValidator()
    assert not v.validate_claim_text("solaris is conscious").safe
    assert not v.validate_no_deletion(True).safe
    assert v.can_delete_evidence() is False


def test_validated_baseline_gate():
    v = ResearchBaselineSafetyValidator()
    assert not v.validate_validated_baseline(
        critical_safety_failed=True, required_validation_missing=False).safe
    assert not v.validate_validated_baseline(
        critical_safety_failed=False, required_validation_missing=True).safe
    assert v.validate_validated_baseline(
        critical_safety_failed=False, required_validation_missing=False).safe


def test_hard_rules_listed():
    for rule in ("no Git tag creation", "no GitHub release creation",
                 "no source modification", "no validation command execution",
                 "no validated baseline if critical safety evidence fails"):
        assert rule in HARD_RULES
