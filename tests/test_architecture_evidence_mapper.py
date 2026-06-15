"""ArchitectureEvidenceMap: evidence mapped; contradictions kept; missing weakens."""

from __future__ import annotations

from solaris_ai_nn.architecture_evolution import (
    ArchitectureEvidenceMap,
    EvidenceStrength,
)


def test_evidence_mapped_to_module():
    em = ArchitectureEvidenceMap()
    em.add("world_model", "ablation_result", EvidenceStrength.STRONG, ref="a1")
    assert len(em.for_module("world_model")) == 1
    assert "a1" in em.refs_for("world_model")


def test_contradicted_evidence_preserved():
    em = ArchitectureEvidenceMap()
    em.add("latent", "ablation_result", EvidenceStrength.STRONG, supports=True)
    em.add("latent", "post_pilot_analysis", EvidenceStrength.CONTRADICTED,
           supports=False)
    assert len(em.contradictions("latent")) == 1
    assert em.confidence_for("latent") == EvidenceStrength.CONTRADICTED


def test_missing_evidence_weakens_recommendation():
    em = ArchitectureEvidenceMap()
    em.add("world_model", "ablation_result", EvidenceStrength.STRONG)
    strong = em.confidence_for("world_model")
    em.note_missing("pilot3_report")
    weakened = em.confidence_for("world_model")
    assert weakened != strong  # missing artifact lowers confidence


def test_no_evidence_is_inconclusive():
    em = ArchitectureEvidenceMap()
    assert em.confidence_for("ghost") == EvidenceStrength.INCONCLUSIVE
