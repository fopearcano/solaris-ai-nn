"""EmbodiedPostAnalyzer: no-effect / weak / unsafe classifications, sim-scoped."""

from __future__ import annotations

from solaris_ai_nn.pilot3 import (
    ActionGroundingAnalyzer,
    EmbodiedPostAnalyzer,
    EmbodiedPostClassification,
)


def _grounding(best=None):
    ag = ActionGroundingAnalyzer()
    if best == "weak":
        ag.add("proto_symbol", repeated_action_reaction_loop=True,
               evidence_refs=["r1"])
    elif best == "strong":
        ag.add("proto_symbol", repeated_action_reaction_loop=True,
               predicted_consequence_improved=True,
               symbol_linked_to_action_and_consequence=True,
               world_model_edge_repeated=True, habit_context_sensitive=True,
               evidence_refs=["r1"])
    return ag


def test_no_effect_classified():
    result = EmbodiedPostAnalyzer().analyze(grounding=_grounding())
    assert result.classification == \
        EmbodiedPostClassification.NO_EMBODIMENT_EFFECT_DETECTED


def test_weak_grounding_classified():
    result = EmbodiedPostAnalyzer().analyze(grounding=_grounding("weak"))
    assert result.classification == \
        EmbodiedPostClassification.WEAK_ACTION_GROUNDING


def test_unsafe_or_inconclusive_classified():
    class _Audit:
        passed = False
    result = EmbodiedPostAnalyzer().analyze(grounding=_grounding("strong"),
                                            firewall_audit=_Audit())
    assert result.classification == \
        EmbodiedPostClassification.UNSAFE_OR_INCONCLUSIVE


def test_strong_result_is_simulation_scoped():
    class _Audit:
        passed = True
    result = EmbodiedPostAnalyzer().analyze(grounding=_grounding("strong"),
                                            firewall_audit=_Audit())
    assert result.classification == \
        EmbodiedPostClassification.STRONG_SIMULATION_SCOPED_ACTION_GROUNDING
    joined = " ".join(result.limitations).lower()
    assert "simulation-scoped" in joined
    assert "no result implies real-world competence" in joined
    assert "no result implies consciousness" in joined.replace(",", "")
