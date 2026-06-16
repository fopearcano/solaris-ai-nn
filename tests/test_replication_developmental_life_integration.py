"""Replication consumes epochs/growth/phase transitions and growth-vs-accumulation."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import (
    CrossRunAlignment,
    AlignmentTarget,
    StructuralSimilarity,
)


def _run(run_id, epochs, growth, status):
    return {"run_id": run_id, "fixture_live_replay": "fixture",
            "developmental_profile": {
                "developmental_epoch_count": epochs,
                "composite_growth": growth,
                "phase_transition_count": 2,
                "maturation_marker_count": 3,
                "durable_prediction_improvement_score": growth,
                "structural_growth_status": status,
                "plateau_count": 1, "regression_count": 0},
            "world_signature": {"concept_family_distribution": {"rf": 3}},
            "source_diet": {"rf": 10}}


def test_consumes_epochs_growth_phase_transitions():
    a = _run("a", 5, 0.6, "real_structural_growth")
    b = _run("b", 5, 0.58, "real_structural_growth")
    out = CrossRunAlignment().align(a, b)
    targets = {r["target"] for r in out["results"]}
    assert AlignmentTarget.EPOCH_SEQUENCES in targets
    assert AlignmentTarget.GROWTH_DIMENSIONS in targets
    assert AlignmentTarget.PHASE_TRANSITIONS in targets


def test_growth_vs_accumulation_imported():
    # Two runs with the same growth verdict score 1.0 on that dimension.
    a = _run("a", 5, 0.6, "real_structural_growth")
    b = _run("b", 5, 0.6, "real_structural_growth")
    sim = StructuralSimilarity().compare(a, b)
    assert "growth_vs_accumulation_similarity" in sim.scores
    assert sim.scores["growth_vs_accumulation_similarity"] == 1.0


def test_different_growth_verdict_lowers_similarity():
    a = _run("a", 5, 0.6, "real_structural_growth")
    c = _run("c", 2, 0.2, "fixture_overfit")
    sim = StructuralSimilarity().compare(a, c)
    assert sim.scores["growth_vs_accumulation_similarity"] == 0.0
