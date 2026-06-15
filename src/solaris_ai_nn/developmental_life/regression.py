"""Regression detection -- visible declines, may recommend auto-regeneration.

The :class:`RegressionDetector` flags developmental regressions (prediction success
decline, sign-drift increase, contamination increase, source corruption, memory gap,
restart discontinuity, ...). Regression must be visible; it does not imply damage
unless evidence supports it, and severe regression may recommend an auto-
regeneration check.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .growth_state import GrowthDimension


class RegressionReason:
    CONCEPT_INSTABILITY = "concept_instability_increase"
    SIGN_DRIFT = "sign_drift_increase"
    PREDICTION_DECLINE = "prediction_success_decline"
    FALSE_PATTERN = "false_pattern_increase"
    ACTION_EFFECT_DECLINE = "action_effect_reliability_decline"
    HABIT_DECLINE = "habit_usefulness_decline"
    INHIBITION_FAILURE = "inhibition_failure"
    CONTAMINATION = "contamination_increase"
    BOUNDARY_CONFUSION = "boundary_confusion_increase"
    SOURCE_CORRUPTION = "source_corruption"
    MEMORY_GAP = "memory_gap"
    RESTART_DISCONTINUITY = "restart_discontinuity"
    OVERLOAD_RECURRENCE = "overload_recurrence"
    UNKNOWN = "unknown"

    ALL = (CONCEPT_INSTABILITY, SIGN_DRIFT, PREDICTION_DECLINE, FALSE_PATTERN,
           ACTION_EFFECT_DECLINE, HABIT_DECLINE, INHIBITION_FAILURE,
           CONTAMINATION, BOUNDARY_CONFUSION, SOURCE_CORRUPTION, MEMORY_GAP,
           RESTART_DISCONTINUITY, OVERLOAD_RECURRENCE, UNKNOWN)


@dataclass
class DevelopmentalRegression:
    """One detected regression (visible; auto-regeneration optional)."""

    reason: str
    regression_id: str = field(
        default_factory=lambda: f"REG_{uuid.uuid4().hex[:8]}")
    magnitude: float = 0.0
    recommend_auto_regeneration: bool = False
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"regression_id": self.regression_id, "reason": self.reason,
                "magnitude": round(self.magnitude, 4),
                "recommend_auto_regeneration": self.recommend_auto_regeneration,
                "evidence_refs": list(self.evidence_refs),
                "note": "regression is made visible; it implies damage only when "
                        "evidence supports it"}


# Dimension -> regression reason when that dimension drops.
_DIM_REGRESSION = {
    GrowthDimension.PREDICTION_SKILL: RegressionReason.PREDICTION_DECLINE,
    GrowthDimension.CONCEPT_STABILITY: RegressionReason.CONCEPT_INSTABILITY,
    GrowthDimension.ACTION_EFFECT_LEARNING:
        RegressionReason.ACTION_EFFECT_DECLINE,
    GrowthDimension.HABIT_USEFULNESS: RegressionReason.HABIT_DECLINE,
    GrowthDimension.CONTAMINATION_RESISTANCE: RegressionReason.CONTAMINATION,
    GrowthDimension.BOUNDARY_CLARITY: RegressionReason.BOUNDARY_CONFUSION,
    GrowthDimension.CONTINUITY_STABILITY: RegressionReason.RESTART_DISCONTINUITY,
}


@dataclass
class RegressionDetector:
    """Detects regressions from dimension drops and status corruption signals."""

    regressions: List[DevelopmentalRegression] = field(default_factory=list)

    def detect(self, *, prior_dims: Dict[str, float],
               current_dims: Dict[str, float],
               statuses: Dict[str, Dict[str, Any]]) -> List[
                   DevelopmentalRegression]:
        self.regressions = []
        for dim, reason in _DIM_REGRESSION.items():
            drop = prior_dims.get(dim, 0.0) - current_dims.get(dim, 0.0)
            if drop >= 0.1:
                self.regressions.append(DevelopmentalRegression(
                    reason=reason, magnitude=round(drop, 4),
                    recommend_auto_regeneration=drop >= 0.3,
                    evidence_refs=[dim]))
        # Source corruption from self-boundary attribution.
        sb = statuses.get("self_boundary", {})
        if float(sb.get("source_attribution_uncertainty_score", 0.0) or 0.0) \
                >= 0.7:
            self.regressions.append(DevelopmentalRegression(
                reason=RegressionReason.SOURCE_CORRUPTION, magnitude=0.5,
                recommend_auto_regeneration=True,
                evidence_refs=["self_boundary:source_uncertainty"]))
        return self.regressions

    def add_restart_discontinuity(self) -> DevelopmentalRegression:
        reg = DevelopmentalRegression(
            reason=RegressionReason.RESTART_DISCONTINUITY, magnitude=0.3,
            evidence_refs=["restart"])
        self.regressions.append(reg)
        return reg

    def to_dict(self) -> Dict[str, Any]:
        return {"regression_count": len(self.regressions),
                "auto_regeneration_recommended": sum(
                    1 for r in self.regressions
                    if r.recommend_auto_regeneration),
                "regressions": [r.to_dict() for r in self.regressions]}
