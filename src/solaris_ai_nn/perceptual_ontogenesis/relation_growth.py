"""Relation growth -- evidence-backed links between proto-concepts.

The :class:`ConceptRelationGrowthEngine` proposes :class:`ConceptRelation`s between
proto-concepts (temporal, predictive, source/modality-sharing, metabolic,
attention, hypothesis, LOGOS). Every relation requires evidence, carries a
weak/moderate/strong strength, tracks a false-relation risk, and never overstates
correlation as causation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .proto_concepts import ProtoConcept


class ConceptRelationType:
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    CO_OCCURS = "co_occurs"
    PREDICTS = "predicts"
    INHIBITS = "inhibits"
    AMPLIFIES = "amplifies"
    REPLACES = "replaces"
    DISAPPEARS_AFTER = "disappears_after"
    APPEARS_AFTER_ABSENCE = "appears_after_absence"
    SHARES_SOURCE = "shares_source"
    SHARES_MODALITY = "shares_modality"
    CROSS_MODAL_LINK = "cross_modal_link"
    METABOLIC_LINK = "metabolic_link"
    ATTENTION_LINK = "attention_link"
    HYPOTHESIS_LINK = "hypothesis_link"
    LOGOS_TENSION_LINK = "LOGOS_tension_link"
    UNKNOWN = "unknown_relation"

    ALL = (PRECEDES, FOLLOWS, CO_OCCURS, PREDICTS, INHIBITS, AMPLIFIES,
           REPLACES, DISAPPEARS_AFTER, APPEARS_AFTER_ABSENCE, SHARES_SOURCE,
           SHARES_MODALITY, CROSS_MODAL_LINK, METABOLIC_LINK, ATTENTION_LINK,
           HYPOTHESIS_LINK, LOGOS_TENSION_LINK, UNKNOWN)


def _strength_band(strength: float) -> str:
    if strength >= 0.66:
        return "strong"
    if strength >= 0.33:
        return "moderate"
    return "weak"


@dataclass
class ConceptRelation:
    """One evidence-backed relation between two concepts (no causation claim)."""

    relation_type: str
    source_concept: str
    target_concept: str
    relation_id: str = field(
        default_factory=lambda: f"REL_{uuid.uuid4().hex[:8]}")
    strength: float = 0.0
    false_relation_risk: float = 0.0
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def strength_band(self) -> str:
        return _strength_band(self.strength)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "source_concept": self.source_concept,
            "target_concept": self.target_concept,
            "strength": round(self.strength, 4),
            "strength_band": self.strength_band,
            "false_relation_risk": round(self.false_relation_risk, 4),
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
            "note": "correlation/structural link only; not a causal claim",
        }


@dataclass
class ConceptRelationGrowthEngine:
    """Grows evidence-backed relations between proto-concepts."""

    relations: Dict[str, ConceptRelation] = field(default_factory=dict)

    def grow(self, concepts: List[ProtoConcept]) -> List[ConceptRelation]:
        """Propose relations from shared structure across concepts."""
        out: List[ConceptRelation] = []
        n = len(concepts)
        for i in range(n):
            for j in range(i + 1, n):
                rel = self._relate(concepts[i], concepts[j])
                if rel is not None:
                    self.relations[rel.relation_id] = rel
                    out.append(rel)
        return out

    def _relate(self, a: ProtoConcept, b: ProtoConcept):
        shared_sources = set(a.source_distribution) & set(b.source_distribution)
        shared_modalities = (set(a.modality_distribution)
                             & set(b.modality_distribution))
        # Strength grows with recurrence evidence; risk falls with it.
        evidence = min(a.recurrence_count, b.recurrence_count)
        strength = min(1.0, 0.2 + 0.2 * evidence)
        risk = round(max(0.0, 1.0 - 0.25 * evidence), 4)

        if shared_sources:
            rtype = ConceptRelationType.SHARES_SOURCE
            ev = [f"source:{s}" for s in sorted(shared_sources)]
        elif shared_modalities and a.dominant_modality != b.dominant_modality:
            rtype = ConceptRelationType.CROSS_MODAL_LINK
            ev = [f"modality:{m}" for m in sorted(shared_modalities)]
        elif shared_modalities:
            rtype = ConceptRelationType.SHARES_MODALITY
            ev = [f"modality:{m}" for m in sorted(shared_modalities)]
        else:
            return None
        return ConceptRelation(
            relation_type=rtype, source_concept=a.concept_id,
            target_concept=b.concept_id, strength=strength,
            false_relation_risk=risk, evidence_refs=ev)

    def add_relation(self, relation_type: str, source: str, target: str,
                     strength: float, evidence_refs: List[str],
                     ) -> ConceptRelation:
        """Add an externally-derived relation (hypothesis/metabolic/LOGOS link)."""
        rel = ConceptRelation(
            relation_type=relation_type, source_concept=source,
            target_concept=target, strength=min(1.0, max(0.0, strength)),
            false_relation_risk=round(max(0.0, 1.0 - strength), 4),
            evidence_refs=list(evidence_refs))
        self.relations[rel.relation_id] = rel
        return rel

    def graph_density(self, concept_count: int) -> float:
        if concept_count < 2:
            return 0.0
        max_edges = concept_count * (concept_count - 1) / 2
        return round(min(1.0, len(self.relations) / max_edges), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relation_count": len(self.relations),
            "relations": [r.to_dict() for r in self.relations.values()],
        }
