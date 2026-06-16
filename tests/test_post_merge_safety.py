"""Post-merge safety: source/Git/GitHub/validation blocked; gated validation."""

from __future__ import annotations

from solaris_ai_nn.post_merge_assimilation import (
    HARD_RULES,
    PostMergeAssimilationSafetyValidator,
)


def test_source_modification_blocked():
    v = PostMergeAssimilationSafetyValidator()
    assert not v.validate_operation("modify source file").safe
    assert v.can_modify_source() is False


def test_git_github_blocked():
    v = PostMergeAssimilationSafetyValidator()
    assert not v.validate_operation("run git merge the branch").safe
    assert not v.validate_operation("call github api").safe
    assert not v.validate_operation("merge pull request").safe
    assert v.can_run_git() is False
    assert v.can_call_github() is False
    assert v.can_merge_or_approve_pr() is False


def test_validation_execution_blocked():
    v = PostMergeAssimilationSafetyValidator()
    assert not v.validate_operation("run pytest now").safe
    assert not v.validate_operation("execute validation").safe
    assert v.can_run_validation() is False


def test_baseline_validation_blocked_when_critical_fails():
    v = PostMergeAssimilationSafetyValidator()
    assert not v.validate_baseline_validation(
        critical_safety_failed=True, critical_evidence_missing=False).safe
    assert not v.validate_baseline_validation(
        critical_safety_failed=False, critical_evidence_missing=True).safe
    assert v.validate_baseline_validation(
        critical_safety_failed=False, critical_evidence_missing=False).safe


def test_evidence_deletion_blocked():
    v = PostMergeAssimilationSafetyValidator()
    assert not v.validate_no_deletion(True).safe
    assert v.can_delete_evidence() is False


def test_hard_rules_listed():
    for rule in ("no source modification", "no Git command execution",
                 "no GitHub call", "no PR creation/approval/merge",
                 "no validation command execution",
                 "no baseline validation if critical safety evidence fails"):
        assert rule in HARD_RULES
