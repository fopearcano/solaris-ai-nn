"""Question pressure -- operational pressure to inspect, not verbal questioning.

A :class:`QuestionPressure` is operational pressure to inspect, compare, wait,
simulate, or preserve an unknown. It is NOT human verbal questioning; it may later
be rendered as human-readable debug text, but the pressure itself is structural.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class QuestionPressureType:
    UNKNOWN_SOURCE = "unknown_source"
    MISSING_EXPECTED_SIGN = "missing_expected_sign"
    CONTRADICTORY_SIGNS = "contradictory_signs"
    AMBIGUOUS_PROTO_CONCEPT = "ambiguous_proto_concept"
    FAILED_PREDICTION = "failed_prediction"
    UNRESOLVED_LOGOS_TENSION = "unresolved_LOGOS_tension"
    UNSTABLE_RELATION = "unstable_relation"
    HIGH_CONTAMINATION = "high_contamination"
    LOW_GROUNDING = "low_grounding"
    SOURCE_SILENCE = "source_silence"
    MODALITY_CONFLICT = "modality_conflict"

    ALL = (UNKNOWN_SOURCE, MISSING_EXPECTED_SIGN, CONTRADICTORY_SIGNS,
           AMBIGUOUS_PROTO_CONCEPT, FAILED_PREDICTION,
           UNRESOLVED_LOGOS_TENSION, UNSTABLE_RELATION, HIGH_CONTAMINATION,
           LOW_GROUNDING, SOURCE_SILENCE, MODALITY_CONFLICT)


# Which internal response each pressure recommends (inspect/compare/wait/...).
_RECOMMENDED_RESPONSE = {
    QuestionPressureType.UNKNOWN_SOURCE: "inspect",
    QuestionPressureType.MISSING_EXPECTED_SIGN: "wait",
    QuestionPressureType.CONTRADICTORY_SIGNS: "compare",
    QuestionPressureType.AMBIGUOUS_PROTO_CONCEPT: "simulate",
    QuestionPressureType.FAILED_PREDICTION: "compare",
    QuestionPressureType.UNRESOLVED_LOGOS_TENSION: "preserve_unknown",
    QuestionPressureType.UNSTABLE_RELATION: "inspect",
    QuestionPressureType.HIGH_CONTAMINATION: "inspect",
    QuestionPressureType.LOW_GROUNDING: "wait",
    QuestionPressureType.SOURCE_SILENCE: "wait",
    QuestionPressureType.MODALITY_CONFLICT: "compare",
}


@dataclass
class QuestionPressure:
    """One operational question pressure (inspect/compare/wait/simulate/preserve)."""

    pressure_type: str
    target_refs: List[str] = field(default_factory=list)
    pressure_id: str = field(default_factory=lambda: f"Q_{uuid.uuid4().hex[:8]}")
    intensity: float = 0.0
    recommended_response: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    resolved: bool = False

    def __post_init__(self) -> None:
        if not self.recommended_response:
            self.recommended_response = _RECOMMENDED_RESPONSE.get(
                self.pressure_type, "inspect")

    def debug_gloss(self) -> str:
        return (f"[debug-gloss] pressure {self.pressure_type} -> "
                f"{self.recommended_response} ({', '.join(self.target_refs)})")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pressure_id": self.pressure_id,
            "pressure_type": self.pressure_type,
            "target_refs": list(self.target_refs),
            "intensity": round(self.intensity, 4),
            "recommended_response": self.recommended_response,
            "evidence_refs": list(self.evidence_refs),
            "resolved": self.resolved,
            "debug_gloss": self.debug_gloss(),
            "note": "operational pressure to inspect/compare/wait/simulate/"
                    "preserve, not a human verbal question",
        }


@dataclass
class QuestionPressureEngine:
    """Derives operational question pressure from cognition signals."""

    pressures: List[QuestionPressure] = field(default_factory=list)

    def generate(self, *, signs: List[Any], failed_predictions: List[Any],
                 logos_tensions: List[Any], anticipation_targets: List[str],
                 observed_targets: List[str]) -> List[QuestionPressure]:
        self.pressures = []
        # Missing expected signs.
        for target in anticipation_targets:
            if target and target not in observed_targets:
                self.pressures.append(QuestionPressure(
                    pressure_type=QuestionPressureType.MISSING_EXPECTED_SIGN,
                    target_refs=[target], intensity=0.5,
                    evidence_refs=["anticipation"]))
        # Failed predictions.
        for p in failed_predictions:
            self.pressures.append(QuestionPressure(
                pressure_type=QuestionPressureType.FAILED_PREDICTION,
                target_refs=[getattr(p, "predicted_target", "")],
                intensity=0.6, evidence_refs=[getattr(p, "prediction_id", "")]))
        # Sign-level: contamination, ambiguity, low grounding.
        for s in signs:
            if getattr(s, "is_contaminated", False):
                self.pressures.append(QuestionPressure(
                    pressure_type=QuestionPressureType.HIGH_CONTAMINATION,
                    target_refs=[s.sign_id], intensity=0.4,
                    evidence_refs=["contamination"]))
            if getattr(s, "is_ambiguous", False):
                self.pressures.append(QuestionPressure(
                    pressure_type=QuestionPressureType.UNSTABLE_RELATION,
                    target_refs=[s.sign_id], intensity=0.4,
                    evidence_refs=["ambiguity"]))
            if getattr(s, "grounding_score", 1.0) < 0.2:
                self.pressures.append(QuestionPressure(
                    pressure_type=QuestionPressureType.LOW_GROUNDING,
                    target_refs=[s.sign_id], intensity=0.3,
                    evidence_refs=["low_grounding"]))
        # Unresolved LOGOS tensions.
        for t in logos_tensions:
            self.pressures.append(QuestionPressure(
                pressure_type=QuestionPressureType.UNRESOLVED_LOGOS_TENSION,
                target_refs=[getattr(t, "tension_id",
                                     getattr(t, "tension_type", "tension"))],
                intensity=0.5, evidence_refs=["logos"]))
        return self.pressures

    def pressure_score(self) -> float:
        if not self.pressures:
            return 0.0
        return round(sum(p.intensity for p in self.pressures)
                     / len(self.pressures), 4)
