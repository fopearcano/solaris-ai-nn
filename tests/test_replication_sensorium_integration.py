"""Replication consumes world signatures; compares sensorium differences."""

from __future__ import annotations

from solaris_ai_nn.developmental_replication import (
    DivergenceDetector,
    DivergenceReason,
    StructuralSimilarity,
)
from solaris_ai_nn.sensorium_lab import SensoriumWorldSignature


def _run_from_signature(run_id, sensorium, sig: SensoriumWorldSignature):
    return {"run_id": run_id, "sensorium_profile": sensorium,
            "fixture_live_replay": "fixture",
            "developmental_profile": {"composite_growth": 0.5,
                                      "structural_growth_status":
                                          "real_structural_growth"},
            "world_signature": sig.to_dict(), "source_diet": {sensorium: 10}}


def test_consumes_world_signatures():
    sig = SensoriumWorldSignature(
        arm_id="nh", condition="non_human",
        concept_family_distribution={"rf": 3, "vib": 2},
        sign_family_distribution={"s1": 2},
        human_label_contamination_score=0.1, boundary_clarity_score=0.7)
    run = _run_from_signature("a", "non_human", sig)
    other = _run_from_signature("b", "non_human", sig)
    result = StructuralSimilarity().compare(run, other)
    assert "concept_family_similarity" in result.scores
    assert result.scores["concept_family_similarity"] == 1.0


def test_compares_sensorium_differences():
    nh = SensoriumWorldSignature(
        arm_id="nh", condition="non_human",
        concept_family_distribution={"rf": 3, "vib": 2},
        human_label_contamination_score=0.1, boundary_clarity_score=0.7)
    hl = SensoriumWorldSignature(
        arm_id="hl", condition="human_like",
        concept_family_distribution={"txt": 5},
        human_label_contamination_score=0.8, boundary_clarity_score=0.3)
    run_nh = _run_from_signature("nh", "non_human", nh)
    run_hl = _run_from_signature("hl", "human_like", hl)
    sim = StructuralSimilarity().compare(run_nh, run_hl)
    # Different sensoriums -> low concept-family similarity.
    assert sim.scores["concept_family_similarity"] < 0.5
    divs = DivergenceDetector().detect(run_nh, run_hl, similarity=sim.overall)
    assert any(d.reason == DivergenceReason.DIFFERENT_SENSORIUM_DIET
               for d in divs)
