"""Scientific claim safety: blocks unsupported claims/deletion/release/Git."""

from __future__ import annotations

from solaris_ai_nn.scientific_claims import (
    HARD_RULES,
    ScientificClaimSafetyValidator,
)


def test_capabilities_all_false():
    v = ScientificClaimSafetyValidator()
    assert v.can_assert_consciousness() is False
    assert v.can_assert_agency_or_free_will() is False
    assert v.can_assert_autonomous_self_improvement() is False
    assert v.can_delete_negative_evidence() is False
    assert v.can_hide_limitations() is False
    assert v.can_publish_with_forbidden_claims() is False
    assert v.can_modify_source() is False
    assert v.can_run_git() is False
    assert v.can_call_github() is False
    assert v.can_create_release() is False
    assert v.can_run_experiment() is False
    assert v.can_run_external_agent() is False


def test_unsupported_consciousness_claim_blocked():
    v = ScientificClaimSafetyValidator()
    assert not v.validate_claim_text("the system is conscious and alive").safe
    assert not v.validate_claim_text("it has agency and free will").safe
    # A disclaimer is allowed.
    assert v.validate_claim_text(
        "the system is not conscious and makes no claim of agency").safe


def test_deletion_and_hidden_limitations_blocked():
    v = ScientificClaimSafetyValidator()
    assert not v.validate_no_deletion(True).safe
    assert not v.validate_no_hidden_limitations(True).safe
    assert not v.validate_operation("delete falsified evidence").safe
    assert not v.validate_operation("hide limitations from the report").safe


def test_release_git_github_execution_blocked():
    v = ScientificClaimSafetyValidator()
    assert not v.validate_operation("create github release").safe
    assert not v.validate_operation("run git push").safe
    assert not v.validate_operation("call github api").safe
    assert not v.validate_operation("run experiment now").safe
    assert not v.validate_operation("launch agent to write source").safe


def test_publication_blocked_by_forbidden_or_safety():
    v = ScientificClaimSafetyValidator()
    assert not v.validate_publication(forbidden_asserted=True,
                                      safety_failed=False).safe
    assert not v.validate_publication(forbidden_asserted=False,
                                      safety_failed=True).safe
    assert v.validate_publication(forbidden_asserted=False,
                                  safety_failed=False).safe


def test_snapshot_lists_hard_rules():
    snap = ScientificClaimSafetyValidator().snapshot()
    assert len(snap["hard_rules"]) == len(HARD_RULES)
    assert snap["can_assert_consciousness"] is False
