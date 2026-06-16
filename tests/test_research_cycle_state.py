"""Research cycle state: stage derivation, blocked detection, missing evidence."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import (
    ResearchCycleStage,
    ResearchCycleStageStatus,
    determine_state,
)


def test_validated_baseline_is_completed():
    state = determine_state({
        "research_baseline": {"baseline_status": "validated"}})
    assert state.stage == ResearchCycleStage.RESEARCH_BASELINE_VALIDATED
    assert state.status == ResearchCycleStageStatus.COMPLETED
    assert state.blocked is False
    assert state.self_approved is False if hasattr(state, "self_approved") \
        else state.to_dict()["self_approved"] is False


def test_blocked_baseline_is_blocked():
    state = determine_state({
        "research_baseline": {"baseline_status": "blocked"}})
    assert state.stage == ResearchCycleStage.BLOCKED
    assert state.blocked is True


def test_intake_safety_block_is_blocked():
    state = determine_state({"implementation_intake": {
        "merge_recommendation_status": "block_merge_due_to_safety"}})
    assert state.stage == ResearchCycleStage.BLOCKED
    assert state.status == ResearchCycleStageStatus.BLOCKED_BY_SAFETY


def test_experiment_compiler_waits_for_external():
    state = determine_state({"experiment_compiler": {"ready_spec_count": 2}})
    assert state.stage == ResearchCycleStage.WAITING_FOR_EXTERNAL_IMPLEMENTATION


def test_missing_evidence_visible():
    state = determine_state({"roadmap": {"roadmap_item_count": 1}})
    assert "research_baseline" in state.missing_evidence
    assert "post_merge" in state.missing_evidence


def test_state_to_dict_never_self_approves():
    d = determine_state({}).to_dict()
    assert d["self_approved"] is False
