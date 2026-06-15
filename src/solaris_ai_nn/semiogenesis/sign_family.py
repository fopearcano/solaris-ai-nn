"""Sign families -- evidence-backed structural groupings, not human taxonomies.

A :class:`SignFamily` groups internal signs that share modality, source, or kind.
Families are structural groupings, NOT human semantic taxonomies; a sign may belong
to several, and membership is always evidence-backed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .signs import InternalSign, SignKind


class SignFamilyType:
    RF = "rf_sign_family"
    ECHO = "echo_sign_family"
    VIBRATION = "vibration_sign_family"
    MAGNETIC = "magnetic_sign_family"
    THERMAL = "thermal_sign_family"
    HUMAN_TEXT = "human_text_sign_family"
    MACHINE_RHYTHM = "machine_rhythm_sign_family"
    ABSENCE = "absence_sign_family"
    CROSS_MODAL = "cross_modal_sign_family"
    METABOLIC = "metabolic_sign_family"
    LOGOS = "LOGOS_sign_family"
    CONTAMINATED_LABEL = "contaminated_label_sign_family"
    MIXED = "mixed_sign_family"

    ALL = (RF, ECHO, VIBRATION, MAGNETIC, THERMAL, HUMAN_TEXT, MACHINE_RHYTHM,
           ABSENCE, CROSS_MODAL, METABOLIC, LOGOS, CONTAMINATED_LABEL, MIXED)


_MODALITY_FAMILY = {
    "radio_frequency": SignFamilyType.RF, "alien_rf": SignFamilyType.RF,
    "echo": SignFamilyType.ECHO, "alien_echo": SignFamilyType.ECHO,
    "vibration": SignFamilyType.VIBRATION,
    "alien_vibration": SignFamilyType.VIBRATION,
    "magnetic": SignFamilyType.MAGNETIC, "thermal": SignFamilyType.THERMAL,
    "human_textual": SignFamilyType.HUMAN_TEXT,
    "machine_rhythm": SignFamilyType.MACHINE_RHYTHM,
}


@dataclass
class SignFamilyRelation:
    """An evidence-backed reason a sign belongs to a family."""

    sign_id: str
    reason: str  # "shared_modality" | "shared_source" | "structural_kind"
    evidence: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SignFamily:
    """A structural cluster of internal signs (not a human taxonomy)."""

    family_type: str
    family_id: str = ""
    members: List[str] = field(default_factory=list)
    relations: List[SignFamilyRelation] = field(default_factory=list)
    modality_distribution: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.family_id:
            self.family_id = f"SIGNFAM_{self.family_type}"

    def add(self, sign: InternalSign, reason: str, evidence: str) -> None:
        if sign.sign_id not in self.members:
            self.members.append(sign.sign_id)
        self.relations.append(SignFamilyRelation(
            sign_id=sign.sign_id, reason=reason, evidence=evidence))
        for mod, n in sign.modality_distribution.items():
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
            "note": "structural sign grouping, not a human semantic taxonomy",
        }


@dataclass
class SignFamilyBuilder:
    """Clusters signs into evidence-backed families (multi-membership ok)."""

    families: Dict[str, SignFamily] = field(default_factory=dict)

    def _family(self, family_type: str) -> SignFamily:
        fam = self.families.get(family_type)
        if fam is None:
            fam = SignFamily(family_type=family_type)
            self.families[family_type] = fam
        return fam

    def build(self, signs: List[InternalSign]) -> List[SignFamily]:
        """(Re)build families from signs; a sign may join several."""
        self.families = {}
        for sign in signs:
            self._place(sign)
        return list(self.families.values())

    def _place(self, sign: InternalSign) -> None:
        placed = False
        if sign.kind == SignKind.ABSENCE:
            self._family(SignFamilyType.ABSENCE).add(
                sign, "structural_kind", "absence sign")
            placed = True
        if sign.is_cross_modal or sign.kind == SignKind.CROSS_MODAL:
            self._family(SignFamilyType.CROSS_MODAL).add(
                sign, "structural_kind", "cross-modal sign")
            placed = True
        if sign.kind == SignKind.METABOLIC:
            self._family(SignFamilyType.METABOLIC).add(
                sign, "structural_kind", "metabolic sign")
            placed = True
        if sign.kind == SignKind.LOGOS_TENSION:
            self._family(SignFamilyType.LOGOS).add(
                sign, "structural_kind", "LOGOS tension sign")
            placed = True
        if sign.is_contaminated:
            self._family(SignFamilyType.CONTAMINATED_LABEL).add(
                sign, "structural_kind", "human-label contaminated")
            placed = True
        for mod in sign.modality_distribution:
            fam_type = _MODALITY_FAMILY.get(mod)
            if fam_type is not None:
                self._family(fam_type).add(
                    sign, "shared_modality", f"modality={mod}")
                placed = True
        if not placed:
            self._family(SignFamilyType.MIXED).add(
                sign, "structural_kind", "unclustered sign")

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
