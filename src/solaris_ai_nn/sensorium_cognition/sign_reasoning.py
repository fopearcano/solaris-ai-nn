"""Sign reasoning -- provisional inference over signs and sign relations.

The :class:`SignReasoner` infers provisional relations between internal signs
(sequence, co-occurrence, absence, contradiction, replacement, source
unreliability, modality conflict, cross-modal unity, drift relevance, failed-
prediction relevance). Inference is provisional, correlation is never causation,
and human glosses are never used as the reasoning substrate -- sign codes and sign
relations are primary.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class SignInferenceType:
    SEQUENCE = "sequence_relation"
    CO_OCCURRENCE = "co_occurrence_relation"
    ABSENCE = "absence_relation"
    CONTRADICTION = "contradiction"
    REPLACEMENT = "replacement"
    SOURCE_UNRELIABILITY = "source_unreliability"
    MODALITY_CONFLICT = "modality_conflict"
    CROSS_MODAL_UNITY = "cross_modal_unity"
    SIGN_DRIFT_RELEVANCE = "sign_drift_relevance"
    FAILED_PREDICTION_RELEVANCE = "failed_prediction_relevance"

    ALL = (SEQUENCE, CO_OCCURRENCE, ABSENCE, CONTRADICTION, REPLACEMENT,
           SOURCE_UNRELIABILITY, MODALITY_CONFLICT, CROSS_MODAL_UNITY,
           SIGN_DRIFT_RELEVANCE, FAILED_PREDICTION_RELEVANCE)


@dataclass
class SignRelationInference:
    """One provisional inferred relation between signs (correlation, not cause)."""

    inference_type: str
    sign_refs: List[str] = field(default_factory=list)
    inference_id: str = field(
        default_factory=lambda: f"INF_{uuid.uuid4().hex[:8]}")
    confidence: float = 0.0
    uncertainty: float = 0.0
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "inference_id": self.inference_id,
            "inference_type": self.inference_type,
            "sign_refs": list(self.sign_refs),
            "confidence": round(self.confidence, 4),
            "uncertainty": round(self.uncertainty, 4),
            "evidence_refs": list(self.evidence_refs),
            "note": "provisional inference; correlation/structure, not causation",
        }


@dataclass
class SignReasoningTrace:
    inferences: List[SignRelationInference] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"inference_count": len(self.inferences),
                "inferences": [i.to_dict() for i in self.inferences]}


# Map a private-syntax relation onto a provisional sign inference.
_SYNTAX_TO_INFERENCE = {
    "sequence": SignInferenceType.SEQUENCE,
    "predicts": SignInferenceType.SEQUENCE,
    "co_occurrence": SignInferenceType.CO_OCCURRENCE,
    "before_absence": SignInferenceType.ABSENCE,
    "after_absence": SignInferenceType.ABSENCE,
    "contradicts": SignInferenceType.CONTRADICTION,
    "replaces": SignInferenceType.REPLACEMENT,
    "unifies": SignInferenceType.CROSS_MODAL_UNITY,
    "splits": SignInferenceType.MODALITY_CONFLICT,
}


@dataclass
class SignReasoner:
    """Infers provisional sign relations from signs and private-syntax patterns."""

    def reason(self, signs: List[Any], patterns: List[Any]) -> SignReasoningTrace:
        trace = SignReasoningTrace()
        by_id = {getattr(s, "sign_id", ""): s for s in signs}

        # 1. Patterns -> provisional relations.
        for pat in patterns:
            itype = _SYNTAX_TO_INFERENCE.get(getattr(pat, "relation", ""),
                                             None)
            if itype is None:
                continue
            strength = float(getattr(pat, "strength", 0.0))
            trace.inferences.append(SignRelationInference(
                inference_type=itype, sign_refs=list(getattr(pat, "signs", [])),
                confidence=strength, uncertainty=round(1.0 - strength, 4),
                evidence_refs=[getattr(pat, "pattern_id", "")]))

        # 2. Sign-level signals -> drift / source / contradiction relevance.
        for s in signs:
            if getattr(s, "is_contaminated", False):
                trace.inferences.append(SignRelationInference(
                    inference_type=SignInferenceType.SOURCE_UNRELIABILITY,
                    sign_refs=[s.sign_id], confidence=0.4, uncertainty=0.6,
                    evidence_refs=["contamination"]))
            if getattr(s, "is_ambiguous", False):
                trace.inferences.append(SignRelationInference(
                    inference_type=SignInferenceType.SIGN_DRIFT_RELEVANCE,
                    sign_refs=[s.sign_id], confidence=0.3, uncertainty=0.7,
                    evidence_refs=["ambiguity"]))

        # 3. Modality conflict across stable signs of different modalities.
        modalities: Dict[str, List[str]] = {}
        for s in signs:
            dm = getattr(s, "dominant_modality", None)
            if dm:
                modalities.setdefault(dm, []).append(s.sign_id)
        mod_keys = list(modalities)
        for i in range(len(mod_keys)):
            for j in range(i + 1, len(mod_keys)):
                trace.inferences.append(SignRelationInference(
                    inference_type=SignInferenceType.MODALITY_CONFLICT,
                    sign_refs=[modalities[mod_keys[i]][0],
                               modalities[mod_keys[j]][0]],
                    confidence=0.3, uncertainty=0.7,
                    evidence_refs=[f"modality:{mod_keys[i]}",
                                   f"modality:{mod_keys[j]}"]))
        return trace
