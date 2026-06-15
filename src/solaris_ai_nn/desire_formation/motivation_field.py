"""Motivation field -- operational field dynamics, no anthropomorphic motivation.

:class:`MotivationField` summarizes the current pushes and desires, the dominant and
competing pressures, and how many desires were inhibited/deferred/satisfied/failed/
safety-blocked. It exposes *why* an internal action was selected or inhibited. This
is operational field dynamics, NOT anthropomorphic motivation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .desire import DesireStatus


@dataclass
class MotivationVector:
    """One contribution to the motivation field (a push/desire pressure)."""

    label: str
    magnitude: float
    direction: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"label": self.label, "magnitude": round(self.magnitude, 4),
                "direction": self.direction}


@dataclass
class MotivationFieldState:
    active_push_count: int = 0
    active_desire_count: int = 0
    dominant_pressure: str = ""
    competing_pressure: str = ""
    inhibited_desire_count: int = 0
    deferred_desire_count: int = 0
    satisfied_desire_count: int = 0
    failed_desire_count: int = 0
    safety_blocked_desire_count: int = 0
    no_action_pressure: float = 0.0
    consolidation_pressure: float = 0.0
    uncertainty_pressure: float = 0.0
    vectors: List[MotivationVector] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active_push_count": self.active_push_count,
            "active_desire_count": self.active_desire_count,
            "dominant_pressure": self.dominant_pressure,
            "competing_pressure": self.competing_pressure,
            "inhibited_desire_count": self.inhibited_desire_count,
            "deferred_desire_count": self.deferred_desire_count,
            "satisfied_desire_count": self.satisfied_desire_count,
            "failed_desire_count": self.failed_desire_count,
            "safety_blocked_desire_count": self.safety_blocked_desire_count,
            "no_action_pressure": round(self.no_action_pressure, 4),
            "consolidation_pressure": round(self.consolidation_pressure, 4),
            "uncertainty_pressure": round(self.uncertainty_pressure, 4),
            "vectors": [v.to_dict() for v in self.vectors],
            "metadata": dict(self.metadata),
            "note": "operational field dynamics; not anthropomorphic motivation",
        }


@dataclass
class MotivationField:
    """Builds the operational motivation-field state from pushes/desires."""

    state: MotivationFieldState = field(default_factory=MotivationFieldState)

    def build(self, pushes: List[Any], desires: List[Any], *,
              valence_gradient: Any = None) -> MotivationFieldState:
        st = MotivationFieldState()
        st.active_push_count = len(pushes)
        st.active_desire_count = sum(
            1 for d in desires
            if getattr(d, "status", "") in (DesireStatus.CANDIDATE,
                                            DesireStatus.ACTIVE))
        st.inhibited_desire_count = sum(
            1 for d in desires
            if getattr(d, "status", "") == DesireStatus.INHIBITED)
        st.deferred_desire_count = sum(
            1 for d in desires
            if getattr(d, "status", "") == DesireStatus.DEFERRED)
        st.satisfied_desire_count = sum(
            1 for d in desires
            if getattr(d, "status", "") == DesireStatus.SATISFIED)
        st.failed_desire_count = sum(
            1 for d in desires
            if getattr(d, "status", "") == DesireStatus.FAILED)
        st.safety_blocked_desire_count = sum(
            1 for d in desires
            if getattr(d, "status", "") == DesireStatus.BLOCKED_BY_SAFETY)
        st.no_action_pressure = round(sum(
            1 for d in desires if getattr(d, "kind", "") == "no_action")
            / max(1, len(desires)), 4)

        # Dominant / competing pressure by push intensity.
        ranked = sorted(pushes, key=lambda p: getattr(p, "intensity", 0.0),
                        reverse=True)
        if ranked:
            st.dominant_pressure = getattr(ranked[0], "source_type", "")
            st.vectors = [MotivationVector(
                label=getattr(p, "source_type", ""),
                magnitude=getattr(p, "intensity", 0.0),
                direction=getattr(p, "metadata", {}).get("valence_direction",
                                                         ""))
                for p in ranked[:8]]
        if len(ranked) > 1:
            st.competing_pressure = getattr(ranked[1], "source_type", "")
        if valence_gradient is not None:
            agg = valence_gradient.by_direction()
            st.uncertainty_pressure = round(agg.get("ambiguous", 0.0), 4)
            st.consolidation_pressure = round(sum(
                v.magnitude for v in getattr(valence_gradient, "valences", [])
                if v.source == "consolidation_pressure"), 4)
        self.state = st
        return st
