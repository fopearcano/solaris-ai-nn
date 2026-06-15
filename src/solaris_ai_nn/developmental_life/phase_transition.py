"""Phase transition -- evidence-backed developmental transitions, conservatively.

The :class:`PhaseTransitionDetector` detects developmental transitions (passive ->
adaptive sensing, proto-concept growth -> sign formation, fixture dependence ->
live grounding, ...). Transitions require evidence, carry low/moderate/high
confidence, report a false-transition risk, and are inconclusive when evidence is
missing.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class TransitionKind:
    PASSIVE_TO_ADAPTIVE = "passive_sensing_to_adaptive_sensing"
    ADAPTIVE_TO_CONCEPT = "adaptive_sensing_to_proto_concept_growth"
    CONCEPT_TO_SIGN = "proto_concept_growth_to_sign_formation"
    SIGN_TO_PREDICTION = "sign_formation_to_prediction_use"
    PREDICTION_TO_ACTION = "prediction_use_to_action_effect_learning"
    ACTION_TO_HABIT = "action_effect_learning_to_habit_formation"
    OVERLOAD_TO_REGULATION = "overload_to_regulation"
    DEPRIVATION_TO_ABSENCE = "deprivation_to_absence_integration"
    FIXTURE_TO_LIVE = "fixture_dependence_to_live_field_grounding"
    LABEL_TO_MODALITY = "human_label_dependence_to_modality_native_grounding"

    ALL = (PASSIVE_TO_ADAPTIVE, ADAPTIVE_TO_CONCEPT, CONCEPT_TO_SIGN,
           SIGN_TO_PREDICTION, PREDICTION_TO_ACTION, ACTION_TO_HABIT,
           OVERLOAD_TO_REGULATION, DEPRIVATION_TO_ABSENCE, FIXTURE_TO_LIVE,
           LABEL_TO_MODALITY)


def _confidence_band(value: float) -> str:
    if value >= 0.66:
        return "high"
    if value >= 0.33:
        return "moderate"
    return "low"


@dataclass
class PhaseTransitionEvidence:
    description: str
    refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"description": self.description, "refs": list(self.refs)}


@dataclass
class DevelopmentalPhaseTransition:
    """One evidence-backed developmental transition (or inconclusive)."""

    kind: str
    transition_id: str = field(
        default_factory=lambda: f"TRN_{uuid.uuid4().hex[:8]}")
    confidence: float = 0.0
    false_transition_risk: float = 0.0
    inconclusive: bool = False
    evidence: List[PhaseTransitionEvidence] = field(default_factory=list)

    @property
    def confidence_band(self) -> str:
        return _confidence_band(self.confidence)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "kind": self.kind,
            "confidence": round(self.confidence, 4),
            "confidence_band": self.confidence_band,
            "false_transition_risk": round(self.false_transition_risk, 4),
            "inconclusive": self.inconclusive,
            "evidence": [e.to_dict() for e in self.evidence],
            "note": "evidence-backed developmental transition; inconclusive when "
                    "evidence is missing",
        }


@dataclass
class PhaseTransitionDetector:
    """Detects developmental transitions across growth snapshots (conservative)."""

    transitions: List[DevelopmentalPhaseTransition] = field(
        default_factory=list)

    def detect(self, *, prior_dims: Dict[str, float],
               current_dims: Dict[str, float]) -> List[
                   DevelopmentalPhaseTransition]:
        self.transitions = []
        if not prior_dims:
            return self.transitions

        def rose(dim: str, threshold: float = 0.1) -> bool:
            return current_dims.get(dim, 0.0) - prior_dims.get(dim, 0.0) \
                >= threshold

        def level(dim: str) -> float:
            return current_dims.get(dim, 0.0)

        checks = [
            (TransitionKind.ADAPTIVE_TO_CONCEPT, "proto_concept_growth"),
            (TransitionKind.CONCEPT_TO_SIGN, "sign_growth"),
            (TransitionKind.SIGN_TO_PREDICTION, "prediction_skill"),
            (TransitionKind.PREDICTION_TO_ACTION, "action_effect_learning"),
            (TransitionKind.ACTION_TO_HABIT, "habit_usefulness"),
            (TransitionKind.PASSIVE_TO_ADAPTIVE, "sensorium_adaptation"),
            (TransitionKind.LABEL_TO_MODALITY, "contamination_resistance"),
        ]
        for kind, dim in checks:
            if rose(dim):
                conf = round(min(1.0, 0.4 + level(dim) * 0.5), 4)
                self.transitions.append(DevelopmentalPhaseTransition(
                    kind=kind, confidence=conf,
                    false_transition_risk=round(1.0 - conf, 4),
                    evidence=[PhaseTransitionEvidence(
                        f"{dim} rose to {level(dim)}", [dim])]))
            elif dim not in current_dims:
                self.transitions.append(DevelopmentalPhaseTransition(
                    kind=kind, confidence=0.0, false_transition_risk=1.0,
                    inconclusive=True,
                    evidence=[PhaseTransitionEvidence("missing evidence", [])]))
        return self.transitions

    def confident_transitions(self) -> List[DevelopmentalPhaseTransition]:
        return [t for t in self.transitions
                if not t.inconclusive and t.confidence >= 0.33]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transition_count": len(self.transitions),
            "confident_transition_count": len(self.confident_transitions()),
            "inconclusive_count": sum(1 for t in self.transitions
                                      if t.inconclusive),
            "transitions": [t.to_dict() for t in self.transitions],
        }
