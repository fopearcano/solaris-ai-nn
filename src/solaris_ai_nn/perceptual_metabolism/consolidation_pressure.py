"""Consolidation pressure -- when to digest rather than keep ingesting.

A :class:`ConsolidationPressureEstimator` weighs overload, receptor fatigue,
repeated invariants, unresolved LOGOS tensions, memory/proto-symbol growth, long
exposure, source silence, and baseline shifts into a single pressure and a
recommendation (none / light / deep / latent-replay / quiet / operator-review).
It does not sleep forever, erases no evidence, and integrates with latent replay
and the developmental runtime if available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class ConsolidationRecommendation:
    NONE = "no_consolidation_needed"
    LIGHT = "light_consolidation"
    DEEP = "deep_consolidation_recommended"
    LATENT_REPLAY = "latent_replay_recommended"
    QUIET = "quiet_mode_recommended"
    OPERATOR_REVIEW = "operator_review_recommended"

    ALL = (NONE, LIGHT, DEEP, LATENT_REPLAY, QUIET, OPERATOR_REVIEW)


@dataclass
class ConsolidationPressureState:
    pressure: float
    recommendation: str
    signals: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"pressure": round(self.pressure, 4),
                "recommendation": self.recommendation,
                "signals": {k: round(v, 4) for k, v in self.signals.items()},
                "note": "does not sleep forever and erases no evidence"}


@dataclass
class ConsolidationPressureEstimator:
    """Estimates how strongly the organism should consolidate."""

    def estimate(self, sensorium: Any, *, overloaded: bool = False,
                 source_silent: bool = False) -> ConsolidationPressureState:
        receptors = list(getattr(sensorium, "receptors", {}).values())
        active = [r for r in receptors if getattr(r, "event_count", 0) > 0]
        fatigue = max((getattr(r, "fatigue", 0.0) for r in active), default=0.0)
        invariants = len(getattr(sensorium, "invariants", None).candidates) \
            if hasattr(sensorium, "invariants") else 0
        protos = len(getattr(sensorium, "proto_symbol_candidates", []))
        tensions = len(getattr(sensorium, "logos_tensions", []))
        hypotheses = len(getattr(sensorium, "hypotheses", []))
        baseline_shifts = len(getattr(sensorium, "baseline_shifts", []))

        signals = {
            "overload": 1.0 if overloaded else 0.0,
            "receptor_fatigue": fatigue,
            "repeated_invariants": min(1.0, invariants / 20.0),
            "unresolved_logos_tension": min(1.0, tensions / 10.0),
            "proto_symbol_growth": min(1.0, protos / 30.0),
            "weak_hypotheses": min(1.0, hypotheses / 30.0),
            "source_silence": 1.0 if source_silent else 0.0,
            "baseline_shift": min(1.0, baseline_shifts / 3.0),
        }
        pressure = round(sum(signals.values()) / len(signals), 4)

        if pressure < 0.15:
            rec = ConsolidationRecommendation.NONE
        elif signals["source_silence"] >= 1.0 and pressure < 0.4:
            rec = ConsolidationRecommendation.QUIET
        elif signals["overload"] >= 1.0 or pressure >= 0.6:
            rec = ConsolidationRecommendation.DEEP
        elif signals["proto_symbol_growth"] >= 0.5 \
                or signals["repeated_invariants"] >= 0.5:
            rec = ConsolidationRecommendation.LATENT_REPLAY
        elif pressure >= 0.3:
            rec = ConsolidationRecommendation.LIGHT
        else:
            rec = ConsolidationRecommendation.LIGHT
        return ConsolidationPressureState(pressure=pressure, recommendation=rec,
                                          signals=signals)

    def latent_replay_recommendations(self, sensorium: Any) -> List[str]:
        """Which kinds of replay would help (recommendation only)."""
        recs: List[str] = []
        if hasattr(sensorium, "invariants") and \
                sensorium.invariants.strong_candidates():
            recs.append("proto_symbol_consolidation_replay")
        if getattr(sensorium, "logos_tensions", []):
            recs.append("unresolved_logos_tension_replay")
        if hasattr(sensorium, "cross_modal") and \
                sensorium.cross_modal.relation_count() > 0:
            recs.append("cross_modal_relation_replay")
        if hasattr(sensorium, "absence") and sensorium.absence.events:
            recs.append("silence_replay")
        if not recs:
            recs.append("light_replay")
        return recs
