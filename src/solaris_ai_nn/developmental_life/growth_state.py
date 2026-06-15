"""Growth state -- structural change across dimensions, not an intelligence score.

:class:`DevelopmentalGrowthState` derives a value per :class:`GrowthDimension` from
the upstream module statuses, and tracks the change (:class:`GrowthSignal`) over
time. Growth means *structural change* -- which may include pruning, decay,
inhibition, and no-op learning -- NOT an intelligence score, and more is not always
better.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class GrowthDimension:
    SENSORIUM_ADAPTATION = "sensorium_adaptation"
    RECEPTOR_STABILITY = "receptor_stability"
    SOURCE_RELIABILITY_LEARNING = "source_reliability_learning"
    PROTO_CONCEPT_GROWTH = "proto_concept_growth"
    CONCEPT_STABILITY = "concept_stability"
    CONCEPT_DECAY_MANAGEMENT = "concept_decay_management"
    SIGN_GROWTH = "sign_growth"
    PRIVATE_SYNTAX_DENSITY = "private_syntax_density"
    PREDICTION_SKILL = "prediction_skill"
    FAILED_PREDICTION_LEARNING = "failed_prediction_learning"
    QUESTION_PRESSURE_RESOLUTION = "question_pressure_resolution"
    ACTION_EFFECT_LEARNING = "action_effect_learning"
    HABIT_USEFULNESS = "habit_usefulness"
    INHIBITION_QUALITY = "inhibition_quality"
    BOUNDARY_CLARITY = "boundary_clarity"
    CONTINUITY_STABILITY = "continuity_stability"
    CONTAMINATION_RESISTANCE = "contamination_resistance"
    CONSOLIDATION_EFFICIENCY = "consolidation_efficiency"

    ALL = (SENSORIUM_ADAPTATION, RECEPTOR_STABILITY,
           SOURCE_RELIABILITY_LEARNING, PROTO_CONCEPT_GROWTH, CONCEPT_STABILITY,
           CONCEPT_DECAY_MANAGEMENT, SIGN_GROWTH, PRIVATE_SYNTAX_DENSITY,
           PREDICTION_SKILL, FAILED_PREDICTION_LEARNING,
           QUESTION_PRESSURE_RESOLUTION, ACTION_EFFECT_LEARNING,
           HABIT_USEFULNESS, INHIBITION_QUALITY, BOUNDARY_CLARITY,
           CONTINUITY_STABILITY, CONTAMINATION_RESISTANCE,
           CONSOLIDATION_EFFICIENCY)


def _g(d: Dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(d.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def dimensions_from_statuses(statuses: Dict[str, Dict[str, Any]],
                             ) -> Dict[str, float]:
    """Compute the 18 growth-dimension values (0..1) from module statuses."""
    met = statuses.get("perceptual_metabolism", {})
    ont = statuses.get("perceptual_ontogenesis", {})
    sem = statuses.get("semiogenesis", {})
    cog = statuses.get("sensorium_cognition", {})
    sb = statuses.get("self_boundary", {})
    ar = statuses.get("action_reaction", {})

    proto = max(1, int(_g(ont, "proto_concept_count", 1)))
    out: Dict[str, float] = {}
    G = GrowthDimension
    out[G.SENSORIUM_ADAPTATION] = min(1.0, _g(met, "source_diet_diversity", 0.0))
    out[G.RECEPTOR_STABILITY] = round(min(1.0, _g(sb, "body_schema_stability",
                                                  0.0)), 4)
    out[G.SOURCE_RELIABILITY_LEARNING] = round(
        1.0 - _g(sb, "source_attribution_uncertainty_score", 0.0), 4)
    out[G.PROTO_CONCEPT_GROWTH] = round(min(
        1.0, _g(ont, "stable_concept_count", 0.0) / 10.0), 4)
    out[G.CONCEPT_STABILITY] = round(
        _g(ont, "stable_concept_count", 0.0) / proto, 4)
    out[G.CONCEPT_DECAY_MANAGEMENT] = round(min(
        1.0, _g(ont, "decaying_concept_count", 0.0) / proto), 4)
    signs = max(1, int(_g(sem, "internal_sign_count", 1)))
    out[G.SIGN_GROWTH] = round(min(
        1.0, _g(sem, "stable_sign_count", 0.0) / 10.0), 4)
    out[G.PRIVATE_SYNTAX_DENSITY] = round(min(
        1.0, _g(sem, "private_syntax_pattern_count", 0.0) / 20.0), 4)
    out[G.PREDICTION_SKILL] = round(_g(cog, "prediction_success_rate", 0.0), 4)
    out[G.FAILED_PREDICTION_LEARNING] = round(min(
        1.0, _g(cog, "failed_prediction_count", 0.0) / 10.0), 4)
    out[G.QUESTION_PRESSURE_RESOLUTION] = round(
        _g(cog, "question_pressure_resolution_rate", 0.0), 4)
    out[G.ACTION_EFFECT_LEARNING] = round(min(
        1.0, _g(ar, "learned_effect_count", 0.0) / 10.0), 4)
    out[G.HABIT_USEFULNESS] = round(min(
        1.0, _g(ar, "strengthened_habit_count", 0.0) / 5.0), 4)
    out[G.INHIBITION_QUALITY] = round(min(
        1.0, _g(ar, "inhibition_count", 0.0) / 5.0), 4)
    out[G.BOUNDARY_CLARITY] = round(_g(sb, "boundary_confidence_score", 0.0), 4)
    out[G.CONTINUITY_STABILITY] = round(max(
        0.0, 1.0 - 0.2 * _g(sb, "continuity_break_count", 0.0)), 4)
    contamination = max(_g(sem, "contaminated_sign_ratio", 0.0),
                        _g(ont, "human_label_contamination_score", 0.0))
    out[G.CONTAMINATION_RESISTANCE] = round(1.0 - contamination, 4)
    out[G.CONSOLIDATION_EFFICIENCY] = round(min(
        1.0, _g(met, "consolidation_pressure_score", 0.0)), 4)
    return out


@dataclass
class GrowthSignal:
    """The change in one growth dimension between two snapshots."""

    dimension: str
    before: float
    after: float

    @property
    def delta(self) -> float:
        return round(self.after - self.before, 4)

    @property
    def direction(self) -> str:
        if self.delta > 0.02:
            return "increase"
        if self.delta < -0.02:
            return "decrease"
        return "stable"

    def to_dict(self) -> Dict[str, Any]:
        return {"dimension": self.dimension, "before": round(self.before, 4),
                "after": round(self.after, 4), "delta": self.delta,
                "direction": self.direction}


@dataclass
class DevelopmentalGrowthState:
    """The current growth-dimension values and signals vs the prior snapshot."""

    dimensions: Dict[str, float] = field(default_factory=dict)
    signals: List[GrowthSignal] = field(default_factory=list)

    def update(self, statuses: Dict[str, Dict[str, Any]], *,
               prior: Optional[Dict[str, float]] = None,
               ) -> List[GrowthSignal]:
        new = dimensions_from_statuses(statuses)
        prior = prior or {}
        self.signals = [GrowthSignal(dim, prior.get(dim, 0.0), new.get(dim, 0.0))
                        for dim in GrowthDimension.ALL]
        self.dimensions = new
        return self.signals

    def composite(self) -> float:
        if not self.dimensions:
            return 0.0
        return round(sum(self.dimensions.values()) / len(self.dimensions), 4)

    def increased_dimensions(self) -> List[str]:
        return [s.dimension for s in self.signals if s.direction == "increase"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimensions": dict(self.dimensions),
            "composite": self.composite(),
            "signals": [s.to_dict() for s in self.signals],
            "increased_dimensions": self.increased_dimensions(),
            "note": "growth = structural change (incl. pruning/decay/inhibition/"
                    "no-op learning); NOT an intelligence score, and more is not "
                    "always better",
        }
