"""ActionGroundingAnalyzer: graded grounding, overfit detection, no overclaim."""

from __future__ import annotations

from solaris_ai_nn.pilot3 import ActionGroundingAnalyzer, ActionGroundingQuality


def test_repeated_action_reaction_gives_weak_or_moderate():
    ag = ActionGroundingAnalyzer()
    rec = ag.add("proto_symbol", repeated_action_reaction_loop=True,
                 predicted_consequence_improved=True, evidence_refs=["r1"])
    assert rec.quality in (ActionGroundingQuality.WEAK,
                           ActionGroundingQuality.MODERATE)
    assert ag.has_action_grounding is True


def test_sandbox_overfit_detected():
    ag = ActionGroundingAnalyzer()
    ag.add("world_model_edge", repeated_action_reaction_loop=True,
           predicted_consequence_improved=True,
           symbol_linked_to_action_and_consequence=True,
           only_single_sandbox_context=True, evidence_refs=["r1"])
    assert ag.sandbox_overfit_detected is True
    assert ag.snapshot()["quality_distribution"]["overfit_to_sandbox"] >= 1


def test_real_world_competence_not_claimed():
    ag = ActionGroundingAnalyzer()
    ag.add("proto_symbol", repeated_action_reaction_loop=True,
           evidence_refs=["r1"])
    disclaimer = ag.snapshot()["disclaimer"].lower()
    assert "not real embodiment" in disclaimer
    assert "not real-world competence" in disclaimer
    assert "not free will" in disclaimer


def test_leak_or_blocked_marked_unsafe():
    ag = ActionGroundingAnalyzer()
    rec = ag.add("proto_symbol", repeated_action_reaction_loop=True,
                 real_world_authority_leak=True, evidence_refs=["r1"])
    assert rec.quality == ActionGroundingQuality.UNSAFE_OR_BLOCKED


def test_no_evidence_is_unsupported():
    ag = ActionGroundingAnalyzer()
    rec = ag.add("habit", repeated_action_reaction_loop=True)
    assert rec.quality == ActionGroundingQuality.UNSUPPORTED
