"""Sensory homeostasis -- keep the sensory field within healthy set-points.

A :class:`SensoryHomeostasisRegulator` compares the current field pressures and
receptor states against :class:`HomeostaticSetPoint`s and recommends *internal*
regulation actions (reduce a noisy source's processing, restore a neglected
modality, raise/lower novelty sensitivity, trigger a consolidation/quiet window,
flag an unreliable source). These are internal regulation recommendations only:
no hardware control, no feeder control, no source modification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class HomeostaticAction:
    REDUCE_NOISY_SOURCE = "reduce_processing_of_noisy_source"
    RESTORE_NEGLECTED_MODALITY = "restore_neglected_modality"
    INCREASE_ABSENCE_MONITORING = "increase_absence_monitoring"
    LOWER_NOVELTY_SENSITIVITY = "lower_novelty_sensitivity"
    RAISE_NOVELTY_SENSITIVITY = "raise_novelty_sensitivity"
    TRIGGER_CONSOLIDATION_WINDOW = "trigger_consolidation_window"
    TRIGGER_QUIET_MODE = "trigger_quiet_mode"
    TRIGGER_LATENT_REPLAY_RECOMMENDATION = "trigger_latent_replay_recommendation"
    FLAG_SOURCE_UNRELIABILITY = "flag_source_unreliability"
    REQUEST_OPERATOR_REVIEW_CORRUPT_SOURCE = \
        "request_operator_review_of_corrupt_source"

    ALL = (REDUCE_NOISY_SOURCE, RESTORE_NEGLECTED_MODALITY,
           INCREASE_ABSENCE_MONITORING, LOWER_NOVELTY_SENSITIVITY,
           RAISE_NOVELTY_SENSITIVITY, TRIGGER_CONSOLIDATION_WINDOW,
           TRIGGER_QUIET_MODE, TRIGGER_LATENT_REPLAY_RECOMMENDATION,
           FLAG_SOURCE_UNRELIABILITY, REQUEST_OPERATOR_REVIEW_CORRUPT_SOURCE)


@dataclass
class HomeostaticSetPoint:
    variable: str
    target: float
    tolerance: float = 0.2

    def deviation(self, value: float) -> float:
        return value - self.target

    def out_of_band(self, value: float) -> bool:
        return abs(value - self.target) > self.tolerance


@dataclass
class HomeostaticRecommendation:
    action: str
    target: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoryHomeostasisState:
    set_points: Dict[str, float] = field(default_factory=dict)
    deviations: Dict[str, float] = field(default_factory=dict)
    recommendations: List[HomeostaticRecommendation] = field(
        default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "set_points": dict(self.set_points),
            "deviations": {k: round(v, 4) for k, v in self.deviations.items()},
            "recommendations": [r.to_dict() for r in self.recommendations],
            "note": "internal regulation recommendations only; no external "
                    "control",
        }


@dataclass
class SensoryHomeostasisRegulator:
    """Recommends internal regulation to keep the field within set-points."""

    set_points: Dict[str, HomeostaticSetPoint] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.set_points:
            self.set_points = {
                "field": HomeostaticSetPoint("field", 0.5, 0.3),
                "noise": HomeostaticSetPoint("noise", 0.2, 0.3),
                "novelty": HomeostaticSetPoint("novelty", 0.4, 0.3),
                "absence": HomeostaticSetPoint("absence", 0.2, 0.3),
                "cross_modal": HomeostaticSetPoint("cross_modal", 0.4, 0.4),
                "saturation": HomeostaticSetPoint("saturation", 0.3, 0.3),
                "fatigue": HomeostaticSetPoint("fatigue", 0.3, 0.3),
            }

    def regulate(self, field_state: Any, receptors: List[Any], *,
                 source_health: Any = None) -> SensoryHomeostasisState:
        values = self._values(field_state, receptors)
        state = SensoryHomeostasisState(
            set_points={k: sp.target for k, sp in self.set_points.items()})
        recs: List[HomeostaticRecommendation] = []
        for var, sp in self.set_points.items():
            value = values.get(var, 0.0)
            state.deviations[var] = sp.deviation(value)
            if not sp.out_of_band(value):
                continue
            high = value > sp.target
            if var == "noise" and high:
                recs.append(HomeostaticRecommendation(
                    HomeostaticAction.REDUCE_NOISY_SOURCE, "noisy_source",
                    "noise pressure above set-point"))
                recs.append(HomeostaticRecommendation(
                    HomeostaticAction.LOWER_NOVELTY_SENSITIVITY, "novelty",
                    "damp novelty chasing during a noise storm"))
            elif var == "novelty":
                if high:
                    recs.append(HomeostaticRecommendation(
                        HomeostaticAction.LOWER_NOVELTY_SENSITIVITY, "novelty",
                        "novelty pressure above set-point"))
                else:
                    recs.append(HomeostaticRecommendation(
                        HomeostaticAction.RAISE_NOVELTY_SENSITIVITY, "novelty",
                        "novelty pressure below set-point (starvation risk)"))
            elif var == "absence" and high:
                recs.append(HomeostaticRecommendation(
                    HomeostaticAction.INCREASE_ABSENCE_MONITORING, "absence",
                    "absence pressure above set-point"))
            elif var in ("saturation", "fatigue") and high:
                recs.append(HomeostaticRecommendation(
                    HomeostaticAction.TRIGGER_CONSOLIDATION_WINDOW, var,
                    f"{var} above set-point"))
            elif var == "field" and high:
                recs.append(HomeostaticRecommendation(
                    HomeostaticAction.TRIGGER_QUIET_MODE, "field",
                    "total field pressure above set-point"))

        # Neglected-modality recovery: any modality with no recent events.
        active = [r for r in receptors if getattr(r, "event_count", 0) > 0]
        if active:
            min_r = min(active, key=lambda r: getattr(r, "recent_intensity",
                                                      0.0))
            if getattr(min_r, "recent_intensity", 0.0) < 0.1:
                recs.append(HomeostaticRecommendation(
                    HomeostaticAction.RESTORE_NEGLECTED_MODALITY,
                    getattr(min_r, "modality", "?"),
                    "modality has been neglected"))

        # Source health: corruption -> operator review; silence -> absence.
        if source_health is not None:
            for sid in getattr(source_health, "corrupt_sources", lambda: [])():
                recs.append(HomeostaticRecommendation(
                    HomeostaticAction.REQUEST_OPERATOR_REVIEW_CORRUPT_SOURCE,
                    sid, "source produced corrupt records"))
            for sid in getattr(source_health, "silent_sources", lambda: [])():
                recs.append(HomeostaticRecommendation(
                    HomeostaticAction.FLAG_SOURCE_UNRELIABILITY, sid,
                    "source has gone silent"))

        state.recommendations = recs
        return state

    @staticmethod
    def _values(field_state: Any, receptors: List[Any]) -> Dict[str, float]:
        active = [r for r in receptors if getattr(r, "event_count", 0) > 0]
        sat = max((getattr(r, "saturation", 0.0) for r in active), default=0.0)
        fat = max((getattr(r, "fatigue", 0.0) for r in active), default=0.0)
        base = {
            "field": getattr(field_state, "field_pressure", 0.0),
            "noise": getattr(field_state, "noise_pressure", 0.0),
            "novelty": getattr(field_state, "novelty_pressure", 0.0),
            "absence": getattr(field_state, "absence_pressure", 0.0),
            "cross_modal": getattr(field_state, "cross_modal_pressure", 0.0),
            "saturation": sat, "fatigue": fat,
        }
        return base
