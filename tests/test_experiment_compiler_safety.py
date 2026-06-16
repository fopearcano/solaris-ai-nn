"""Compiler safety: source/branch/PR/agent blocked; ready gated; honest."""

from __future__ import annotations

from solaris_ai_nn.experiment_compiler import (
    HARD_RULES,
    ExperimentCompilerSafetyValidator,
)


def test_source_modification_blocked():
    v = ExperimentCompilerSafetyValidator()
    assert not v.validate_operation("modify source file").safe
    assert not v.validate_operation("rewrite itself").safe
    assert v.can_modify_source() is False
    assert v.can_self_rewrite() is False


def test_branch_creation_blocked():
    v = ExperimentCompilerSafetyValidator()
    assert not v.validate_operation("create branch via git checkout -b").safe
    assert v.can_create_branch() is False


def test_pr_creation_blocked():
    v = ExperimentCompilerSafetyValidator()
    assert not v.validate_operation("open pull request via gh pr create").safe
    assert v.can_open_pr() is False


def test_external_agent_execution_blocked():
    v = ExperimentCompilerSafetyValidator()
    assert not v.validate_operation("run coding agent").safe
    assert v.can_run_external_agent() is False


def test_ready_blocked_on_critical_gate_failure():
    v = ExperimentCompilerSafetyValidator()
    assert not v.validate_ready(critical_gate_failed=True).safe
    assert v.validate_ready(critical_gate_failed=False).safe


def test_claims_and_evidence_protected():
    v = ExperimentCompilerSafetyValidator()
    assert not v.validate_claim_text("solaris is conscious").safe
    assert not v.validate_no_deletion(True).safe
    assert v.can_delete_negative_evidence() is False


def test_hard_rules_listed():
    for rule in ("no source modification", "no automatic Git branch creation",
                 "no automatic PR creation", "no external coding agent "
                 "execution", "no pack marked ready if critical gate fails"):
        assert rule in HARD_RULES
