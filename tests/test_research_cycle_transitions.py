"""Cycle transitions: gate-checked, advisory, no external action/source change."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import (
    CycleTransitionEngine,
    ResearchCycleStage,
)


def test_gates_passed_permits_forward_transition():
    eng = CycleTransitionEngine()
    ts = eng.propose(ResearchCycleStage.BASELINE_SELECTED,
                     gates_passed=True, blocked=False)
    assert ts[0].to_stage == ResearchCycleStage.ROADMAP_DEFINED
    assert ts[0].allowed is True


def test_gates_not_passed_blocks_transition():
    eng = CycleTransitionEngine()
    ts = eng.propose(ResearchCycleStage.BASELINE_SELECTED,
                     gates_passed=False, blocked=False)
    assert ts[0].allowed is False


def test_blocked_transitions_to_blocked():
    eng = CycleTransitionEngine()
    ts = eng.propose(ResearchCycleStage.IMPLEMENTATION_AUDITED,
                     gates_passed=True, blocked=True)
    assert ts[0].to_stage == ResearchCycleStage.BLOCKED


def test_to_dict_declares_no_external_action():
    eng = CycleTransitionEngine()
    out = eng.to_dict(eng.propose(ResearchCycleStage.ROADMAP_DEFINED,
                                  gates_passed=True, blocked=False))
    assert all(t["executes_external_action"] is False
               for t in out["transitions"])
    assert all(t["modifies_source"] is False for t in out["transitions"])


def test_is_allowed_rules():
    assert CycleTransitionEngine.is_allowed(
        ResearchCycleStage.BASELINE_SELECTED, ResearchCycleStage.ROADMAP_DEFINED)
    assert CycleTransitionEngine.is_allowed(
        ResearchCycleStage.ROADMAP_DEFINED, ResearchCycleStage.BLOCKED)
    assert not CycleTransitionEngine.is_allowed(
        ResearchCycleStage.BASELINE_SELECTED, ResearchCycleStage.CYCLE_COMPLETE)
