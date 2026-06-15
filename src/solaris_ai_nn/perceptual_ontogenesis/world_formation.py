"""World formation -- the observable internal structural world Solaris builds.

The :class:`WorldFormationBuilder` summarizes the proto-concepts, families, and
relations into a :class:`SensoriumWorld`: how many concepts are active/stable/
decaying, the family distribution, the relation-graph density, cross-modal and
absence integration, modality dominance, human-label contamination, and which
structures are prediction/compression/source-reliability supported.

This is an *observable internal structural world*, NOT a subjective world, NOT
qualia, and NOT proof of experience.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .proto_concepts import ProtoConcept, ProtoConceptStatus


@dataclass
class WorldFormationState:
    active_concept_count: int = 0
    stable_concept_count: int = 0
    decaying_concept_count: int = 0
    rejected_concept_count: int = 0
    concept_family_distribution: Dict[str, int] = field(default_factory=dict)
    relation_graph_density: float = 0.0
    cross_modal_integration: float = 0.0
    absence_integration: float = 0.0
    modality_dominance: Dict[str, int] = field(default_factory=dict)
    human_label_contamination: float = 0.0
    prediction_supported_structures: int = 0
    compression_supported_structures: int = 0
    source_reliability_structures: int = 0
    unknown_unresolved_structures: int = 0
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_concept_count": self.active_concept_count,
            "stable_concept_count": self.stable_concept_count,
            "decaying_concept_count": self.decaying_concept_count,
            "rejected_concept_count": self.rejected_concept_count,
            "concept_family_distribution": dict(
                self.concept_family_distribution),
            "relation_graph_density": round(self.relation_graph_density, 4),
            "cross_modal_integration": round(self.cross_modal_integration, 4),
            "absence_integration": round(self.absence_integration, 4),
            "modality_dominance": dict(self.modality_dominance),
            "human_label_contamination": round(
                self.human_label_contamination, 4),
            "prediction_supported_structures":
                self.prediction_supported_structures,
            "compression_supported_structures":
                self.compression_supported_structures,
            "source_reliability_structures": self.source_reliability_structures,
            "unknown_unresolved_structures": self.unknown_unresolved_structures,
            "limitations": list(self.limitations),
            "note": "observable internal structural world; NOT a subjective "
                    "world, NOT qualia, NOT proof of experience",
        }


@dataclass
class SensoriumWorld:
    """The internal structural world summary plus its density score."""

    state: WorldFormationState
    formation_density: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"formation_density": round(self.formation_density, 4),
                "state": self.state.to_dict()}


@dataclass
class WorldFormationBuilder:
    """Builds the observable structural world from concepts/families/relations."""

    def build(self, concepts: List[ProtoConcept], *,
              family_distribution: Dict[str, int],
              relation_density: float) -> SensoriumWorld:
        active = [c for c in concepts
                  if c.status not in (ProtoConceptStatus.REJECTED,
                                      ProtoConceptStatus.MERGED)]
        stable = [c for c in concepts
                  if c.status == ProtoConceptStatus.STABLE]
        decaying = [c for c in concepts
                    if c.status == ProtoConceptStatus.DECAYING]
        rejected = [c for c in concepts
                    if c.status == ProtoConceptStatus.REJECTED]

        modality_dominance: Dict[str, int] = {}
        for c in active:
            for mod, n in c.modality_distribution.items():
                modality_dominance[mod] = modality_dominance.get(mod, 0) + n

        cross_modal = sum(1 for c in active if c.is_cross_modal)
        absence = sum(1 for c in active if c.is_absence_based)
        denom = max(1, len(active))
        contamination = (sum(c.human_label_contamination_score for c in active)
                         / denom)

        state = WorldFormationState(
            active_concept_count=len(active),
            stable_concept_count=len(stable),
            decaying_concept_count=len(decaying),
            rejected_concept_count=len(rejected),
            concept_family_distribution=dict(family_distribution),
            relation_graph_density=relation_density,
            cross_modal_integration=round(cross_modal / denom, 4),
            absence_integration=round(absence / denom, 4),
            modality_dominance=modality_dominance,
            human_label_contamination=round(contamination, 4),
            prediction_supported_structures=sum(
                1 for c in active if c.prediction_utility >= 0.5),
            compression_supported_structures=sum(
                1 for c in active if c.compression_utility >= 0.5),
            source_reliability_structures=sum(
                1 for c in active if c.source_distribution),
            unknown_unresolved_structures=sum(
                1 for c in active if c.kind == "unknown"),
            limitations=[
                "structural world only; not subjective experience or qualia",
                "stable structures are provisional; do not prove understanding",
            ])
        # Formation density: a blend of stability ratio and relation density.
        stable_ratio = len(stable) / denom
        formation_density = round(
            0.5 * stable_ratio + 0.5 * relation_density, 4)
        return SensoriumWorld(state=state, formation_density=formation_density)
