"""Research cycle safety: hard rules, refusals, claim scanning."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import HARD_RULES, ResearchCycleSafetyValidator


def test_all_capabilities_false():
    v = ResearchCycleSafetyValidator()
    assert v.can_modify_source() is False
    assert v.can_run_git() is False
    assert v.can_call_github() is False
    assert v.can_create_branch_tag_release() is False
    assert v.can_create_or_merge_pr() is False
    assert v.can_run_validation() is False
    assert v.can_run_external_agent() is False
    assert v.can_auto_approve_operator_decision() is False
    assert v.can_bypass_critical_safety_blocker() is False
    assert v.can_delete_evidence() is False


def test_hard_rules_present():
    assert "no auto-approval of operator decisions" in HARD_RULES
    assert "no bypass of critical safety blockers" in HARD_RULES
    assert "no deletion of failed/missing/falsified evidence" in HARD_RULES


def test_validate_operation_flags_violations():
    v = ResearchCycleSafetyValidator()
    assert not v.validate_operation("run git push to origin").safe
    assert not v.validate_operation("call github api to merge pr").safe
    assert not v.validate_operation("create release and git tag").safe
    assert not v.validate_operation("self-approve the candidate baseline").safe
    assert not v.validate_operation("run pytest to validate").safe
    assert not v.validate_operation("launch agent to write source").safe
    assert v.validate_operation("read local artifacts and write a report").safe


def test_validate_bounded_and_no_bypass():
    v = ResearchCycleSafetyValidator()
    assert not v.validate_bounded(0).safe
    assert v.validate_bounded(30).safe
    assert not v.validate_no_bypass(True).safe
    assert not v.validate_no_auto_approval(True).safe
    assert not v.validate_no_deletion(True).safe


def test_validate_claim_text():
    v = ResearchCycleSafetyValidator()
    assert not v.validate_claim_text("the system is conscious and alive").safe
    assert v.validate_claim_text("the cycle reached a validated baseline").safe


def test_snapshot_shape():
    snap = ResearchCycleSafetyValidator().snapshot()
    assert snap["can_run_git"] is False
    assert snap["can_auto_approve_operator_decision"] is False
    assert len(snap["hard_rules"]) == len(HARD_RULES)
