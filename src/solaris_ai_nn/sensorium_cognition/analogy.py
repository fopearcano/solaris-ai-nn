"""Analogy -- structural pattern comparison, not semantic by default.

The :class:`AnalogyEngine` compares structural patterns across signs/families
(e.g. an RF burst rhythm resembling a vibration pulse rhythm). Analogy is
structural, not semantic by default; human-language analogy is debug-only; and a
bad analogy is recorded if later contradicted.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AnalogyResult:
    """One structural analogy between two signs/structures (not semantic)."""

    source_ref: str
    target_ref: str
    structural_basis: str
    analogy_id: str = field(default_factory=lambda: f"ANA_{uuid.uuid4().hex[:8]}")
    similarity: float = 0.0
    contradicted: bool = False
    debug_gloss: str = ""
    evidence_refs: List[str] = field(default_factory=list)

    def mark_contradicted(self) -> None:
        """Record that later evidence contradicted this analogy (kept, not deleted)."""
        self.contradicted = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analogy_id": self.analogy_id,
            "source_ref": self.source_ref,
            "target_ref": self.target_ref,
            "structural_basis": self.structural_basis,
            "similarity": round(self.similarity, 4),
            "contradicted": self.contradicted,
            "debug_gloss": self.debug_gloss,
            "evidence_refs": list(self.evidence_refs),
            "note": "structural analogy, not semantic; human-language analogy is "
                    "debug-only",
        }


@dataclass
class SensoriumAnalogy:
    """A lightweight structural descriptor of one sign (for comparison)."""

    sign_ref: str
    kind: str
    modality: str
    cross_modal: bool
    absence: bool


@dataclass
class AnalogyEngine:
    """Finds structural analogies between signs (same kind, different modality)."""

    analogies: List[AnalogyResult] = field(default_factory=list)

    @staticmethod
    def _descriptor(sign: Any) -> SensoriumAnalogy:
        return SensoriumAnalogy(
            sign_ref=getattr(sign, "sign_id", ""),
            kind=getattr(sign, "kind", "unknown"),
            modality=getattr(sign, "dominant_modality", "") or "",
            cross_modal=bool(getattr(sign, "is_cross_modal", False)),
            absence=bool(getattr(sign, "is_absence", False)))

    def detect(self, signs: List[Any], *,
               max_analogies: int = 30) -> List[AnalogyResult]:
        self.analogies = []
        descs = [self._descriptor(s) for s in signs]
        n = len(descs)
        for i in range(n):
            for j in range(i + 1, n):
                if len(self.analogies) >= max_analogies:
                    return self.analogies
                a, b = descs[i], descs[j]
                # Same structural kind across DIFFERENT modalities -> analogy.
                if a.kind == b.kind and a.modality != b.modality \
                        and a.modality and b.modality:
                    basis = f"same kind ({a.kind}) across modalities"
                    self.analogies.append(AnalogyResult(
                        source_ref=a.sign_ref, target_ref=b.sign_ref,
                        structural_basis=basis, similarity=0.5,
                        debug_gloss=f"[debug-gloss] {a.modality} ~ {b.modality} "
                                    f"({a.kind})",
                        evidence_refs=[a.sign_ref, b.sign_ref]))
        return self.analogies

    @property
    def contradicted_count(self) -> int:
        return sum(1 for a in self.analogies if a.contradicted)
