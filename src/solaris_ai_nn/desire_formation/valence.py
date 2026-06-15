"""Valence -- operational priority gradients, NOT feelings or pleasure/pain.

A :class:`SensoriumValence` is an operational priority signal derived from a
sensorium/metabolism/cognition/boundary state. Valence directions (attractive,
aversive, stabilizing, destabilizing, ambiguous, unknown) describe internal
*priority*, not emotion: valence influences internal attention, simulation,
consolidation, and readiness only, and it can never authorize real-world action.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class ValenceSource:
    SENSORY_NOVELTY = "sensory_novelty"
    SENSORY_OVERLOAD = "sensory_overload"
    SENSORY_DEPRIVATION = "sensory_deprivation"
    ABSENCE_PRESSURE = "absence_pressure"
    RHYTHM_STABILITY = "rhythm_stability"
    SOURCE_RELIABILITY = "source_reliability"
    SOURCE_CORRUPTION = "source_corruption"
    PREDICTION_SUCCESS = "prediction_success"
    PREDICTION_FAILURE = "prediction_failure"
    LOGOS_TENSION = "logos_tension"
    CONCEPT_STABILITY = "concept_stability"
    CONCEPT_DECAY = "concept_decay"
    SIGN_UTILITY = "sign_utility"
    SIGN_DRIFT = "sign_drift"
    BOUNDARY_UNCERTAINTY = "boundary_uncertainty"
    SIMULATION_BOUNDARY_WARNING = "simulation_boundary_warning"
    CONTINUITY_BREAK = "continuity_break"
    CONSOLIDATION_PRESSURE = "consolidation_pressure"

    ALL = (SENSORY_NOVELTY, SENSORY_OVERLOAD, SENSORY_DEPRIVATION,
           ABSENCE_PRESSURE, RHYTHM_STABILITY, SOURCE_RELIABILITY,
           SOURCE_CORRUPTION, PREDICTION_SUCCESS, PREDICTION_FAILURE,
           LOGOS_TENSION, CONCEPT_STABILITY, CONCEPT_DECAY, SIGN_UTILITY,
           SIGN_DRIFT, BOUNDARY_UNCERTAINTY, SIMULATION_BOUNDARY_WARNING,
           CONTINUITY_BREAK, CONSOLIDATION_PRESSURE)


class ValenceDirection:
    ATTRACTIVE = "attractive"
    AVERSIVE = "aversive"
    STABILIZING = "stabilizing"
    DESTABILIZING = "destabilizing"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"

    ALL = (ATTRACTIVE, AVERSIVE, STABILIZING, DESTABILIZING, AMBIGUOUS,
           UNKNOWN)


# Each source's default operational direction (priority, not feeling).
_SOURCE_DIRECTION = {
    ValenceSource.SENSORY_NOVELTY: ValenceDirection.ATTRACTIVE,
    ValenceSource.SENSORY_OVERLOAD: ValenceDirection.AVERSIVE,
    ValenceSource.SENSORY_DEPRIVATION: ValenceDirection.ATTRACTIVE,
    ValenceSource.ABSENCE_PRESSURE: ValenceDirection.ATTRACTIVE,
    ValenceSource.RHYTHM_STABILITY: ValenceDirection.STABILIZING,
    ValenceSource.SOURCE_RELIABILITY: ValenceDirection.STABILIZING,
    ValenceSource.SOURCE_CORRUPTION: ValenceDirection.AVERSIVE,
    ValenceSource.PREDICTION_SUCCESS: ValenceDirection.STABILIZING,
    ValenceSource.PREDICTION_FAILURE: ValenceDirection.DESTABILIZING,
    ValenceSource.LOGOS_TENSION: ValenceDirection.DESTABILIZING,
    ValenceSource.CONCEPT_STABILITY: ValenceDirection.STABILIZING,
    ValenceSource.CONCEPT_DECAY: ValenceDirection.DESTABILIZING,
    ValenceSource.SIGN_UTILITY: ValenceDirection.ATTRACTIVE,
    ValenceSource.SIGN_DRIFT: ValenceDirection.DESTABILIZING,
    ValenceSource.BOUNDARY_UNCERTAINTY: ValenceDirection.AMBIGUOUS,
    ValenceSource.SIMULATION_BOUNDARY_WARNING: ValenceDirection.AVERSIVE,
    ValenceSource.CONTINUITY_BREAK: ValenceDirection.DESTABILIZING,
    ValenceSource.CONSOLIDATION_PRESSURE: ValenceDirection.STABILIZING,
}


@dataclass
class SensoriumValence:
    """One operational valence signal (priority, not feeling)."""

    source: str
    direction: str
    magnitude: float = 0.0
    valence_id: str = field(default_factory=lambda: f"VAL_{uuid.uuid4().hex[:8]}")
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valence_id": self.valence_id,
            "source": self.source,
            "direction": self.direction,
            "magnitude": round(self.magnitude, 4),
            "evidence_refs": list(self.evidence_refs),
            "note": "operational priority signal, NOT a feeling/emotion and NOT "
                    "pleasure/pain",
        }


@dataclass
class ValenceGradient:
    """The aggregate valence gradient across all current valence signals."""

    valences: List[SensoriumValence] = field(default_factory=list)

    def add(self, source: str, magnitude: float,
            evidence_refs: List[str] = None) -> SensoriumValence:
        direction = _SOURCE_DIRECTION.get(source, ValenceDirection.UNKNOWN)
        v = SensoriumValence(source=source, direction=direction,
                             magnitude=max(0.0, min(1.0, magnitude)),
                             evidence_refs=list(evidence_refs or []))
        self.valences.append(v)
        return v

    def by_direction(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for v in self.valences:
            out[v.direction] = round(out.get(v.direction, 0.0) + v.magnitude, 4)
        return out

    def dominant_direction(self) -> str:
        agg = self.by_direction()
        if not agg:
            return ValenceDirection.UNKNOWN
        return max(agg, key=agg.get)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valence_count": len(self.valences),
            "by_direction": self.by_direction(),
            "dominant_direction": self.dominant_direction(),
            "valences": [v.to_dict() for v in self.valences],
            "note": "operational priority gradient; valence is not emotion",
        }


@dataclass
class ValenceAssessment:
    """Derives a valence gradient from the upstream operational states."""

    gradient: ValenceGradient = field(default_factory=ValenceGradient)

    def assess(self, *, metabolism: Dict[str, Any] = None,
               cognition: Dict[str, Any] = None,
               self_boundary: Dict[str, Any] = None,
               logos_tension_count: int = 0) -> ValenceGradient:
        self.gradient = ValenceGradient()
        m = metabolism or {}
        c = cognition or {}
        sb = self_boundary or {}

        if m.get("overload_state"):
            self.gradient.add(ValenceSource.SENSORY_OVERLOAD, 0.8,
                              ["metabolism:overload"])
        if m.get("deprivation_state"):
            self.gradient.add(ValenceSource.SENSORY_DEPRIVATION, 0.6,
                              ["metabolism:deprivation"])
        if m.get("novelty_appetite_pressure", 0.0):
            self.gradient.add(ValenceSource.SENSORY_NOVELTY,
                              float(m.get("novelty_appetite_pressure", 0.0)),
                              ["metabolism:novelty"])
        if m.get("consolidation_pressure_score", 0.0):
            self.gradient.add(ValenceSource.CONSOLIDATION_PRESSURE,
                              float(m.get("consolidation_pressure_score", 0.0)),
                              ["metabolism:consolidation"])

        if c.get("failed_prediction_count", 0):
            self.gradient.add(ValenceSource.PREDICTION_FAILURE,
                              min(1.0, 0.2 * c.get("failed_prediction_count",
                                                   0)),
                              ["cognition:failed_prediction"])
        if c.get("prediction_success_rate", 0.0):
            self.gradient.add(ValenceSource.PREDICTION_SUCCESS,
                              float(c.get("prediction_success_rate", 0.0)),
                              ["cognition:prediction_success"])
        if c.get("question_pressure_count", 0):
            self.gradient.add(ValenceSource.ABSENCE_PRESSURE,
                              min(1.0, 0.1 * c.get("question_pressure_count",
                                                   0)),
                              ["cognition:question_pressure"])

        if logos_tension_count:
            self.gradient.add(ValenceSource.LOGOS_TENSION,
                              min(1.0, 0.2 * logos_tension_count), ["logos"])

        unc = float(sb.get("source_attribution_uncertainty_score", 0.0) or 0.0)
        if unc:
            self.gradient.add(ValenceSource.BOUNDARY_UNCERTAINTY, unc,
                              ["self_boundary:uncertainty"])
        if sb.get("simulation_boundary_warning_count", 0):
            self.gradient.add(ValenceSource.SIMULATION_BOUNDARY_WARNING,
                              min(1.0, 0.3 * sb.get(
                                  "simulation_boundary_warning_count", 0)),
                              ["self_boundary:sim_warning"])
        if sb.get("continuity_break_count", 0):
            self.gradient.add(ValenceSource.CONTINUITY_BREAK,
                              min(1.0, 0.3 * sb.get("continuity_break_count",
                                                    0)),
                              ["self_boundary:continuity_break"])
        return self.gradient
