"""Pilot-2 comparative design -- nursery vs sensory vs mixed, cautiously.

The :class:`ComparativeRunDesign` defines comparison arms (nursery-only,
sensory-membrane-only, mixed, fixture replay, post-Pilot-1 reference) and
compares developmental metrics across them. It never claims causality from one
run: differences are reported as "observed difference" / "candidate effect" /
"associated with", and a missing comparable baseline makes a result
inconclusive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ComparisonArm:
    NURSERY_ONLY_BASELINE = "nursery_only_baseline"
    SENSORY_MEMBRANE_ONLY = "sensory_membrane_only"
    MIXED_NURSERY_MEMBRANE = "mixed_nursery_membrane"
    FIXTURE_REPLAY = "fixture_replay"
    POST_PILOT1_REFERENCE = "post_pilot1_reference"

    ALL = (NURSERY_ONLY_BASELINE, SENSORY_MEMBRANE_ONLY,
           MIXED_NURSERY_MEMBRANE, FIXTURE_REPLAY, POST_PILOT1_REFERENCE)


# The metrics compared across arms.
COMPARISON_METRICS = (
    "proto_symbol_emergence", "symbol_stability", "ambiguity_ratio",
    "world_model_node_count", "prediction_trend", "mysterium_trend",
    "active_sampling_usefulness", "hypothesis_support_ratio",
    "logos_tension_count", "autoregeneration_degradation",
    "memory_compression", "provenance_completeness", "safety_incidents",
)
# Metrics where a lower value is the better direction.
_LOWER_IS_BETTER = frozenset({"ambiguity_ratio", "autoregeneration_degradation",
                             "safety_incidents", "logos_tension_count"})


@dataclass
class ComparisonMetric:
    """One metric compared between two arms (cautious language only)."""

    metric: str
    baseline_value: float
    comparison_value: float

    @property
    def delta(self) -> float:
        return round(self.comparison_value - self.baseline_value, 6)

    @property
    def direction(self) -> str:
        if self.delta == 0:
            return "no observed difference"
        better = (self.delta < 0) if self.metric in _LOWER_IS_BETTER \
            else (self.delta > 0)
        return "candidate improvement" if better \
            else "candidate regression"

    def to_dict(self) -> Dict[str, Any]:
        return {"metric": self.metric, "baseline_value": self.baseline_value,
                "comparison_value": self.comparison_value, "delta": self.delta,
                "direction": self.direction}


@dataclass
class ComparisonResult:
    """The cautious comparison of one arm against a baseline arm."""

    baseline_arm: str
    comparison_arm: str
    metrics: List[ComparisonMetric] = field(default_factory=list)
    inconclusive: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_arm": self.baseline_arm,
            "comparison_arm": self.comparison_arm,
            "inconclusive": self.inconclusive,
            "metrics": [m.to_dict() for m in self.metrics],
            "notes": self.notes,
            "disclaimer": "Differences are observed associations from a "
                          "single run, not proven causal effects.",
        }


@dataclass
class ComparativeRunDesign:
    """Holds arm summaries and produces cautious comparisons."""

    arms: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def set_arm(self, arm: str, metrics: Dict[str, Any]) -> None:
        if arm not in ComparisonArm.ALL:
            raise ValueError(f"unknown comparison arm {arm!r}")
        self.arms[arm] = dict(metrics)

    def compare(self, baseline_arm: str,
                comparison_arm: str) -> ComparisonResult:
        result = ComparisonResult(baseline_arm=baseline_arm,
                                  comparison_arm=comparison_arm)
        base = self.arms.get(baseline_arm)
        comp = self.arms.get(comparison_arm)
        if base is None or comp is None:
            result.inconclusive = True
            result.notes.append(
                "missing comparable baseline; result is inconclusive")
            return result
        for metric in COMPARISON_METRICS:
            if metric in base or metric in comp:
                result.metrics.append(ComparisonMetric(
                    metric=metric,
                    baseline_value=float(base.get(metric, 0.0) or 0.0),
                    comparison_value=float(comp.get(metric, 0.0) or 0.0)))
        if not result.metrics:
            result.inconclusive = True
            result.notes.append("no overlapping metrics; inconclusive")
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {"arms": sorted(self.arms),
                "arm_count": len(self.arms),
                "metrics_compared": list(COMPARISON_METRICS)}
