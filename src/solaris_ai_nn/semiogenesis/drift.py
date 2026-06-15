"""Sign drift -- making changes in a sign's grounding visible, not hidden.

The :class:`SignDriftDetector` compares a sign's current grounding against a prior
snapshot and reports meaning/source/modality/human-label/family/relation drift,
ambiguity increase, over-generalization, and over-specialization. Drift is not
automatically bad -- it must be *visible* -- and severe drift can recommend a LOGOS
tension or concept split.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .signs import InternalSign


class SignDrift:
    MEANING = "sign_meaning_drift"
    SOURCE = "sign_source_drift"
    MODALITY = "modality_drift"
    HUMAN_LABEL = "human_label_drift"
    FAMILY = "family_drift"
    RELATION = "relation_drift"
    AMBIGUITY_INCREASE = "ambiguity_increase"
    OVERGENERALIZATION = "overgeneralization"
    OVERSPECIALIZATION = "overspecialization"

    ALL = (MEANING, SOURCE, MODALITY, HUMAN_LABEL, FAMILY, RELATION,
           AMBIGUITY_INCREASE, OVERGENERALIZATION, OVERSPECIALIZATION)


@dataclass
class SignDriftResult:
    sign_id: str
    drifted: bool
    kinds: List[str] = field(default_factory=list)
    severity: float = 0.0
    recommend_logos_tension: bool = False
    recommend_concept_split: bool = False
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_id": self.sign_id,
            "drifted": self.drifted,
            "kinds": list(self.kinds),
            "severity": round(self.severity, 4),
            "recommend_logos_tension": self.recommend_logos_tension,
            "recommend_concept_split": self.recommend_concept_split,
            "detail": dict(self.detail),
            "note": "drift is made visible; drift is not automatically bad",
        }


@dataclass
class SignDriftDetector:
    """Detects drift between a prior and current snapshot of a sign."""

    severe_threshold: float = 0.6
    _prior: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def snapshot(self, sign: InternalSign) -> Dict[str, Any]:
        return {
            "modalities": set(sign.modality_distribution),
            "sources": set(sign.source_distribution),
            "ambiguity": sign.ambiguity_score,
            "contamination": float(bool(sign.contamination_flags)),
            "relation_utility": sign.relation_utility,
        }

    def observe(self, sign: InternalSign) -> SignDriftResult:
        """Record a sign and report drift against its previous observation."""
        cur = self.snapshot(sign)
        prev = self._prior.get(sign.sign_id)
        self._prior[sign.sign_id] = cur
        if prev is None:
            return SignDriftResult(sign_id=sign.sign_id, drifted=False)

        kinds: List[str] = []
        severity = 0.0
        new_modalities = cur["modalities"] - prev["modalities"]
        lost_modalities = prev["modalities"] - cur["modalities"]
        if new_modalities:
            kinds.append(SignDrift.MODALITY)
            severity += 0.3
        if cur["sources"] != prev["sources"]:
            kinds.append(SignDrift.SOURCE)
            severity += 0.2
        if cur["ambiguity"] > prev["ambiguity"]:
            kinds.append(SignDrift.AMBIGUITY_INCREASE)
            severity += cur["ambiguity"] - prev["ambiguity"]
        if cur["contamination"] > prev["contamination"]:
            kinds.append(SignDrift.HUMAN_LABEL)
            severity += 0.3
        if len(cur["modalities"]) > len(prev["modalities"]) + 1:
            kinds.append(SignDrift.OVERGENERALIZATION)
            severity += 0.2
        if lost_modalities and not cur["modalities"]:
            kinds.append(SignDrift.OVERSPECIALIZATION)
            severity += 0.2
        if cur["relation_utility"] != prev["relation_utility"]:
            kinds.append(SignDrift.RELATION)
            severity += 0.1

        severity = round(min(1.0, severity), 4)
        severe = severity >= self.severe_threshold
        return SignDriftResult(
            sign_id=sign.sign_id, drifted=bool(kinds), kinds=kinds,
            severity=severity,
            recommend_logos_tension=severe,
            recommend_concept_split=(severe and SignDrift.OVERGENERALIZATION
                                     in kinds),
            detail={"new_modalities": sorted(new_modalities)})
