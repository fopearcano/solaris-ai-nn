"""ConceptRelationGrowthEngine: evidence-backed; false-risk; no causation claim."""

from __future__ import annotations

from solaris_ai_nn.perceptual_ontogenesis import (
    ConceptRelationGrowthEngine,
    ConceptRelationType,
    ProtoConcept,
    ProtoConceptKind,
)


def _concept(modality, source, recurrence=4):
    return ProtoConcept(kind=ProtoConceptKind.MODALITY_NATIVE,
                        modality_distribution={modality: recurrence},
                        source_distribution={source: recurrence},
                        recurrence_count=recurrence)


def test_relation_created_from_evidence():
    a = _concept("radio_frequency", "rf_feed")
    b = _concept("radio_frequency", "rf_feed")
    rels = ConceptRelationGrowthEngine().grow([a, b])
    assert len(rels) == 1
    assert rels[0].relation_type == ConceptRelationType.SHARES_SOURCE
    assert rels[0].evidence_refs  # evidence required


def test_false_relation_risk_tracked():
    a = _concept("radio_frequency", "rf_feed", recurrence=1)
    b = _concept("radio_frequency", "rf_feed", recurrence=1)
    rel = ConceptRelationGrowthEngine().grow([a, b])[0]
    # Low recurrence => high false-relation risk.
    assert rel.false_relation_risk > 0.5
    assert rel.strength_band in ("weak", "moderate", "strong")


def test_causality_not_overclaimed():
    a = _concept("radio_frequency", "rf_feed")
    b = _concept("radio_frequency", "rf_feed")
    rel = ConceptRelationGrowthEngine().grow([a, b])[0]
    assert "not a causal claim" in rel.to_dict()["note"]


def test_cross_modal_link_when_modalities_differ():
    a = _concept("radio_frequency", "shared_feed")
    b = _concept("vibration", "shared_feed")
    rel = ConceptRelationGrowthEngine().grow([a, b])[0]
    # Shared source dominates; either way it is evidence-backed, not causal.
    assert rel.relation_type in (ConceptRelationType.SHARES_SOURCE,
                                 ConceptRelationType.CROSS_MODAL_LINK)


def test_graph_density_bounded():
    engine = ConceptRelationGrowthEngine()
    concepts = [_concept("radio_frequency", "rf_feed") for _ in range(4)]
    engine.grow(concepts)
    assert 0.0 <= engine.graph_density(len(concepts)) <= 1.0
