"""Intake safety: source/merge/PR/GitHub/Git/agent blocked; honest snapshot."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import (
    HARD_RULES,
    ImplementationIntakeSafetyValidator,
)


def test_source_modification_blocked():
    v = ImplementationIntakeSafetyValidator()
    assert not v.validate_operation("modify source file").safe
    assert v.can_modify_source() is False


def test_merge_execution_blocked():
    v = ImplementationIntakeSafetyValidator()
    assert not v.validate_operation("merge pull request").safe
    assert not v.validate_operation("git merge the branch").safe
    assert v.can_merge() is False


def test_pr_github_git_call_blocked():
    v = ImplementationIntakeSafetyValidator()
    assert not v.validate_operation("open pull request via gh pr create").safe
    assert not v.validate_operation("call github api").safe
    assert not v.validate_operation("run git checkout -b x").safe
    assert v.can_create_or_approve_pr() is False
    assert v.can_call_github() is False
    assert v.can_run_git() is False


def test_external_agent_execution_blocked():
    v = ImplementationIntakeSafetyValidator()
    assert not v.validate_operation("run coding agent").safe
    assert v.can_run_external_agent() is False


def test_self_approval_and_deletion_blocked():
    v = ImplementationIntakeSafetyValidator()
    assert v.can_approve_itself() is False
    assert not v.validate_no_deletion(True).safe
    assert v.can_delete_evidence() is False
    assert not v.validate_ready(critical_gate_failed=True).safe


def test_hard_rules_listed():
    for rule in ("no source modification", "no merge execution",
                 "no PR creation", "no GitHub call",
                 "no external coding agent execution",
                 "no ready recommendation if critical safety gate fails"):
        assert rule in HARD_RULES
