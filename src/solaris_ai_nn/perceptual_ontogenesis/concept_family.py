"""Concept families -- evidence-backed structural clusters, not human taxonomies.

A :class:`ConceptFamily` groups proto-concepts that share modality, source, or
structural kind. Families are structural clusters, NOT human taxonomies by
default; a concept may belong to multiple families, and every family membership is
evidence-backed (shared modality/source/kind), never a semantic label.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .proto_concepts import ProtoConcept, ProtoConceptKind


class ConceptFamilyType:
    RF = "rf_family"
    ECHO = "echo_family"
    VIBRATION = "vibration_family"
    MAGNETIC = "magnetic_family"
    THERMAL = "thermal_family"
    HUMAN_TEXT = "human_text_family"
    MACHINE_RHYTHM = "machine_rhythm_family"
    ABSENCE = "absence_family"
    CROSS_MODAL = "cross_modal_family"
    METABOLIC = "metabolic_family"
    CONTAMINATED_LABEL = "contaminated_label_family"
    MIXED = "mixed_family"

    ALL = (RF, ECHO, VIBRATION, MAGNETIC, THERMAL, HUMAN_TEXT, MACHINE_RHYTHM,
           ABSENCE, CROSS_MODAL, METABOLIC, CONTAMINATED_LABEL, MIXED)


_MODALITY_FAMILY = {
    "radio_frequency": ConceptFamilyType.RF,
    "alien_rf": ConceptFamilyType.RF,
    "echo": ConceptFamilyType.ECHO,
    "alien_echo": ConceptFamilyType.ECHO,
    "vibration": ConceptFamilyType.VIBRATION,
    "alien_vibration": ConceptFamilyType.VIBRATION,
    "magnetic": ConceptFamilyType.MAGNETIC,
    "thermal": ConceptFamilyType.THERMAL,
    "human_textual": ConceptFamilyType.HUMAN_TEXT,
    "machine_rhythm": ConceptFamilyType.MACHINE_RHYTHM,
}


@dataclass
class ConceptFamilyRelation:
    """An evidence-backed reason a concept belongs to a family."""

    concept_id: str
    reason: str  # "shared_modality" | "shared_source" | "structural_kind"
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ConceptFamily:
    """A structural cluster of proto-concepts (not a human taxonomy)."""

    family_type: str
    family_id: str = ""
    members: List[str] = field(default_factory=list)
    relations: List[ConceptFamilyRelation] = field(default_factory=list)
    modality_distribution: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.family_id:
            self.family_id = f"FAMILY_{self.family_type}"

    def add(self, concept: ProtoConcept, reason: str, evidence: str) -> None:
        if concept.concept_id not in self.members:
            self.members.append(concept.concept_id)
        self.relations.append(ConceptFamilyRelation(
            concept_id=concept.concept_id, reason=reason, evidence=evidence))
        for mod, n in concept.modality_distribution.items():
            self.modality_distribution[mod] = (
                self.modality_distribution.get(mod, 0) + n)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family_id": self.family_id,
            "family_type": self.family_type,
            "member_count": len(self.members),
            "members": list(self.members),
            "relations": [r.to_dict() for r in self.relations],
            "modality_distribution": dict(self.modality_distribution),
            "note": "structural cluster, not a human taxonomy",
        }


@dataclass
class ConceptFamilyBuilder:
    """Clusters concepts into evidence-backed families (multi-membership ok)."""

    families: Dict[str, ConceptFamily] = field(default_factory=dict)

    def _family(self, family_type: str) -> ConceptFamily:
        fam = self.families.get(family_type)
        if fam is None:
            fam = ConceptFamily(family_type=family_type)
            self.families[family_type] = fam
        return fam

    def build(self, concepts: List[ProtoConcept]) -> List[ConceptFamily]:
        """(Re)build families from concepts; a concept may join several."""
        self.families = {}
        for concept in concepts:
            self._place(concept)
        return list(self.families.values())

    def _place(self, concept: ProtoConcept) -> None:
        placed = False
        # 1. Structural-kind families (absence/cross-modal/metabolic/contaminated).
        if concept.kind == ProtoConceptKind.ABSENCE_BASED:
            self._family(ConceptFamilyType.ABSENCE).add(
                concept, "structural_kind", "absence-based concept")
            placed = True
        if concept.is_cross_modal or concept.kind == ProtoConceptKind.CROSS_MODAL:
            self._family(ConceptFamilyType.CROSS_MODAL).add(
                concept, "structural_kind", "cross-modal concept")
            placed = True
        if concept.kind == ProtoConceptKind.METABOLIC_STATE_BASED:
            self._family(ConceptFamilyType.METABOLIC).add(
                concept, "structural_kind", "metabolic-state concept")
            placed = True
        if concept.is_contaminated:
            self._family(ConceptFamilyType.CONTAMINATED_LABEL).add(
                concept, "structural_kind", "human-label contaminated")
            placed = True
        # 2. Modality families (a concept may match several modalities).
        for mod in concept.modality_distribution:
            fam_type = _MODALITY_FAMILY.get(mod)
            if fam_type is not None:
                self._family(fam_type).add(
                    concept, "shared_modality", f"modality={mod}")
                placed = True
        # 3. Anything else lands in the mixed family.
        if not placed:
            self._family(ConceptFamilyType.MIXED).add(
                concept, "structural_kind", "unclustered concept")

    def dominant_family(self) -> str:
        if not self.families:
            return ""
        return max(self.families.values(),
                   key=lambda f: len(f.members)).family_type

    def distribution(self) -> Dict[str, int]:
        return {ft: len(f.members) for ft, f in self.families.items()}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family_count": len(self.families),
            "dominant_family": self.dominant_family(),
            "distribution": self.distribution(),
            "families": [f.to_dict() for f in self.families.values()],
        }
