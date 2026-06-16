"""Replication consumes concept/sign/cognition/desire/action metrics."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import StructuralSimilarity


def _run(run_id, concepts, signs, habit):
    return {"run_id": run_id, "fixture_live_replay": "fixture",
            "developmental_profile": {
                "composite_growth": 0.6,
                "durable_action_effect_learning_score": 0.5,
                "structural_growth_status": "real_structural_growth"},
            "stack_metrics": {"concept_family_distribution": concepts,
                              "sign_family_distribution": signs,
                              "habit_profile": habit},
            "world_signature": {},
            "source_diet": {"rf": 10}}


def test_consumes_stack_metrics():
    a = _run("a", {"rf": 3, "vib": 2}, {"s1": 2}, {"h1": 1})
    b = _run("b", {"rf": 3, "vib": 2}, {"s1": 2}, {"h1": 1})
    result = StructuralSimilarity().compare(a, b)
    # Concept/sign/habit families come from stack_metrics when no world sig.
    assert result.scores["concept_family_similarity"] == 1.0
    assert result.scores["sign_family_similarity"] == 1.0
    assert result.scores["habit_formation_similarity"] == 1.0


def test_similarity_uses_action_effect_metric():
    a = _run("a", {"rf": 3}, {"s1": 2}, {"h1": 1})
    b = _run("b", {"rf": 3}, {"s1": 2}, {"h1": 1})
    result = StructuralSimilarity().compare(a, b)
    assert "action_effect_learning_similarity" in result.scores
