"""Push -- pre-desire operational pressure, not conscious intention.

A :class:`SensoriumPush` is a pre-desire pressure formed from a valence gradient and
the upstream state. Push is NOT conscious intention; it preserves its evidence, and
it may decay without ever leading to an action.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class PushSource:
    HIGH_NOVELTY = "high_novelty_pressure"
    UNRESOLVED_ABSENCE = "unresolved_absence"
    FAILED_PREDICTION = "failed_prediction"
    STRONG_INVARIANT = "strong_invariant_candidate"
    UNSTABLE_CONCEPT = "unstable_proto_concept"
    SIGN_AMBIGUITY = "sign_ambiguity"
    LOGOS_TENSION = "logos_tension"
    SOURCE_SILENCE = "source_silence"
    SOURCE_CORRUPTION = "source_corruption"
    RECEPTOR_FATIGUE = "receptor_fatigue"
    OVERLOAD = "overload"
    DEPRIVATION = "deprivation"
    BOUNDARY_AMBIGUITY = "boundary_ambiguity"
    CONTINUITY_BREAK = "continuity_break"
    CONSOLIDATION_PRESSURE = "consolidation_pressure"

    ALL = (HIGH_NOVELTY, UNRESOLVED_ABSENCE, FAILED_PREDICTION,
           STRONG_INVARIANT, UNSTABLE_CONCEPT, SIGN_AMBIGUITY, LOGOS_TENSION,
           SOURCE_SILENCE, SOURCE_CORRUPTION, RECEPTOR_FATIGUE, OVERLOAD,
           DEPRIVATION, BOUNDARY_AMBIGUITY, CONTINUITY_BREAK,
           CONSOLIDATION_PRESSURE)


class PushIntensity:
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

    @staticmethod
    def band(value: float) -> str:
        if value >= 0.66:
            return PushIntensity.HIGH
        if value >= 0.33:
            return PushIntensity.MODERATE
        return PushIntensity.LOW


# Maps valence sources / metabolism flags onto push sources.
_VALENCE_TO_PUSH = {
    "sensory_novelty": PushSource.HIGH_NOVELTY,
    "sensory_overload": PushSource.OVERLOAD,
    "sensory_deprivation": PushSource.DEPRIVATION,
    "absence_pressure": PushSource.UNRESOLVED_ABSENCE,
    "source_corruption": PushSource.SOURCE_CORRUPTION,
    "prediction_failure": PushSource.FAILED_PREDICTION,
    "logos_tension": PushSource.LOGOS_TENSION,
    "concept_decay": PushSource.UNSTABLE_CONCEPT,
    "sign_drift": PushSource.SIGN_AMBIGUITY,
    "boundary_uncertainty": PushSource.BOUNDARY_AMBIGUITY,
    "continuity_break": PushSource.CONTINUITY_BREAK,
    "consolidation_pressure": PushSource.CONSOLIDATION_PRESSURE,
}


@dataclass
class SensoriumPush:
    """One pre-desire operational pressure (not conscious intention)."""

    source_type: str
    push_id: str = field(default_factory=lambda: f"PUSH_{uuid.uuid4().hex[:8]}")
    source_refs: List[str] = field(default_factory=list)
    intensity: float = 0.0
    valence_refs: List[str] = field(default_factory=list)
    urgency: float = 0.0
    decay_rate: float = 0.1
    evidence_refs: List[str] = field(default_factory=list)
    uncertainty: float = 0.0
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.limitations:
            self.limitations = [
                "pre-desire operational pressure, not conscious intention",
                "may decay without any action",
            ]

    @property
    def intensity_band(self) -> str:
        return PushIntensity.band(self.intensity)

    def decay(self) -> None:
        self.intensity = round(max(0.0, self.intensity - self.decay_rate), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "push_id": self.push_id,
            "source_type": self.source_type,
            "source_refs": list(self.source_refs),
            "intensity": round(self.intensity, 4),
            "intensity_band": self.intensity_band,
            "valence_refs": list(self.valence_refs),
            "urgency": round(self.urgency, 4),
            "decay_rate": self.decay_rate,
            "evidence_refs": list(self.evidence_refs),
            "uncertainty": round(self.uncertainty, 4),
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
            "note": "push is pre-desire; not conscious intention",
        }


@dataclass
class PushFormationEngine:
    """Forms pushes from the valence gradient (pre-desire pressure)."""

    pushes: List[SensoriumPush] = field(default_factory=list)

    def form(self, gradient: Any, *,
             max_pushes: int = 50) -> List[SensoriumPush]:
        self.pushes = []
        for v in getattr(gradient, "valences", []):
            if len(self.pushes) >= max_pushes:
                break
            source = _VALENCE_TO_PUSH.get(v.source)
            if source is None or v.magnitude <= 0.0:
                continue
            self.pushes.append(SensoriumPush(
                source_type=source, source_refs=list(v.evidence_refs),
                intensity=v.magnitude, valence_refs=[v.valence_id],
                urgency=round(min(1.0, v.magnitude), 4),
                uncertainty=round(1.0 - v.magnitude, 4),
                evidence_refs=list(v.evidence_refs),
                metadata={"valence_direction": v.direction}))
        return self.pushes

    def to_dict(self) -> Dict[str, Any]:
        return {"push_count": len(self.pushes),
                "pushes": [p.to_dict() for p in self.pushes]}
