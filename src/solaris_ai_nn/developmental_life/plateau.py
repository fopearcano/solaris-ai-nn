"""Plateau detection -- no-growth stretches, with internal/report-only advice.

The :class:`PlateauDetector` flags developmental plateaus (no new stable concepts,
prediction not improving, repeated no-effect actions, narrow source diet, ...).
A plateau is NOT failure; it may recommend a source-diet change, consolidation, or a
sensorium study -- recommendations are internal/report-only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class PlateauReason:
    NO_NEW_CONCEPTS = "no_new_stable_concepts"
    NO_USEFUL_SIGNS = "no_useful_signs"
    PREDICTION_NOT_IMPROVING = "prediction_not_improving"
    REPEATED_NO_EFFECT = "repeated_no_effect_actions"
    REPEATED_NO_OP = "repeated_no_op_without_utility"
    NARROW_SOURCE_DIET = "source_diet_too_narrow"
    OVERLOAD_BLOCKING = "overload_blocking_growth"
    DEPRIVATION_HIGH = "deprivation_too_high"
    CONTAMINATION_HIGH = "contamination_too_high"
    FIXTURE_DEPENDENCE = "excessive_fixture_dependence"
    HABIT_RIGIDITY = "habit_rigidity"
    BOUNDARY_UNCERTAINTY = "boundary_uncertainty"
    UNKNOWN = "unknown"

    ALL = (NO_NEW_CONCEPTS, NO_USEFUL_SIGNS, PREDICTION_NOT_IMPROVING,
           REPEATED_NO_EFFECT, REPEATED_NO_OP, NARROW_SOURCE_DIET,
           OVERLOAD_BLOCKING, DEPRIVATION_HIGH, CONTAMINATION_HIGH,
           FIXTURE_DEPENDENCE, HABIT_RIGIDITY, BOUNDARY_UNCERTAINTY, UNKNOWN)


_REASON_RECOMMENDATION = {
    PlateauReason.NARROW_SOURCE_DIET: "broaden the source diet",
    PlateauReason.NO_NEW_CONCEPTS: "run a quiet consolidation window",
    PlateauReason.PREDICTION_NOT_IMPROVING: "schedule a sensorium study",
    PlateauReason.CONTAMINATION_HIGH: "reduce human-label weight",
    PlateauReason.OVERLOAD_BLOCKING: "increase consolidation / no-op",
}


@dataclass
class DevelopmentalPlateau:
    """One detected plateau (not failure; recommendation is report-only)."""

    reason: str
    plateau_id: str = field(default_factory=lambda: f"PLT_{uuid.uuid4().hex[:8]}")
    span_ticks: int = 0
    recommendation: str = ""
    evidence_refs: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.recommendation:
            self.recommendation = _REASON_RECOMMENDATION.get(
                self.reason, "continue exposure; observe")

    def to_dict(self) -> Dict[str, Any]:
        return {"plateau_id": self.plateau_id, "reason": self.reason,
                "span_ticks": self.span_ticks,
                "recommendation": self.recommendation,
                "evidence_refs": list(self.evidence_refs),
                "note": "plateau is not failure; recommendation is internal/"
                        "report-only"}


@dataclass
class PlateauDetector:
    """Detects plateaus from the composite-growth trajectory and statuses."""

    plateaus: List[DevelopmentalPlateau] = field(default_factory=list)
    stale_ticks: int = field(default=0, init=False)

    def detect(self, *, composite_history: List[float],
               statuses: Dict[str, Dict[str, Any]],
               window: int = 3) -> List[DevelopmentalPlateau]:
        self.plateaus = []
        if len(composite_history) < window:
            return self.plateaus
        recent = composite_history[-window:]
        # No meaningful change in composite growth over the window.
        if max(recent) - min(recent) < 0.02:
            self.stale_ticks += 1
            met = statuses.get("perceptual_metabolism", {})
            ar = statuses.get("action_reaction", {})
            reason = PlateauReason.NO_NEW_CONCEPTS
            if met.get("overload_state"):
                reason = PlateauReason.OVERLOAD_BLOCKING
            elif float(met.get("source_diet_diversity", 1.0) or 1.0) < 0.3:
                reason = PlateauReason.NARROW_SOURCE_DIET
            elif int(ar.get("no_effect_action_count", 0) or 0) >= 2:
                reason = PlateauReason.REPEATED_NO_EFFECT
            self.plateaus.append(DevelopmentalPlateau(
                reason=reason, span_ticks=window,
                evidence_refs=["composite_growth_flat"]))
        else:
            self.stale_ticks = 0
        return self.plateaus

    def to_dict(self) -> Dict[str, Any]:
        return {"plateau_count": len(self.plateaus),
                "stale_ticks": self.stale_ticks,
                "plateaus": [p.to_dict() for p in self.plateaus]}
