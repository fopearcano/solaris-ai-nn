"""Pilot-3 comparative design -- perception vs simulated action grounding.

The :class:`Pilot3ComparativeDesign` defines comparison arms (no-body internal,
read-only sensory, GridWorld simulated body, mixed sensory+GridWorld, dry-run
motor trace) and compares action-grounding metrics across them. It never claims
causality from one run: differences are "observed difference" / "candidate
effect"; simulation evidence is simulation-scoped; and real-world action
evidence is always zero.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class Pilot3ComparisonArm:
    NO_BODY_INTERNAL_ONLY = "no_body_internal_only"
    READ_ONLY_SENSORY = "read_only_sensory"
    GRIDWORLD_SIMULATED_BODY = "gridworld_simulated_body"
    MIXED_SENSORY_GRIDWORLD = "mixed_sensory_gridworld"
    DRY_RUN_MOTOR_TRACE = "dry_run_motor_trace"

    ALL = (NO_BODY_INTERNAL_ONLY, READ_ONLY_SENSORY,
           GRIDWORLD_SIMULATED_BODY, MIXED_SENSORY_GRIDWORLD,
           DRY_RUN_MOTOR_TRACE)


# The metrics compared across arms (all simulation-scoped).
COMPARISON_METRICS = (
    "action_grounded_proto_symbol_count", "action_grounded_symbol_stability",
    "simulated_consequence_prediction_accuracy", "world_model_action_edge_count",
    "habit_loop_stability", "active_perception_usefulness",
    "hypothesis_testability", "logos_action_inhibition_tension_count",
    "mysterium_change_after_exploration", "veto_block_count",
    "action_loop_count", "non_actuation_proof_score", "resource_growth",
    "safety_incidents",
)
# Metrics where a lower value is the better direction.
_LOWER_IS_BETTER = frozenset({"veto_block_count", "action_loop_count",
                             "mysterium_change_after_exploration",
                             "resource_growth", "safety_incidents"})


@dataclass
class Pilot3ComparisonMetric:
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
        return "candidate improvement" if better else "candidate regression"

    def to_dict(self) -> Dict[str, Any]:
        return {"metric": self.metric, "baseline_value": self.baseline_value,
                "comparison_value": self.comparison_value, "delta": self.delta,
                "direction": self.direction}


@dataclass
class Pilot3ComparisonResult:
    """The cautious comparison of one arm against a baseline arm."""

    baseline_arm: str
    comparison_arm: str
    metrics: List[Pilot3ComparisonMetric] = field(default_factory=list)
    inconclusive: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_arm": self.baseline_arm,
            "comparison_arm": self.comparison_arm,
            "inconclusive": self.inconclusive,
            "metrics": [m.to_dict() for m in self.metrics],
            "notes": self.notes,
            "real_world_action_evidence": 0,
            "disclaimer": "Differences are observed associations from a single "
                          "simulated run, not proven causal effects; all "
                          "evidence is simulation-scoped.",
        }


@dataclass
class Pilot3ComparativeDesign:
    """Holds arm summaries and produces cautious, simulation-scoped comparisons."""

    arms: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def set_arm(self, arm: str, metrics: Dict[str, Any]) -> None:
        if arm not in Pilot3ComparisonArm.ALL:
            raise ValueError(f"unknown comparison arm {arm!r}")
        # Real-world action evidence is always zero, regardless of input.
        clean = dict(metrics)
        clean["real_world_action_evidence"] = 0
        self.arms[arm] = clean

    def compare(self, baseline_arm: str,
                comparison_arm: str) -> Pilot3ComparisonResult:
        result = Pilot3ComparisonResult(baseline_arm=baseline_arm,
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
                result.metrics.append(Pilot3ComparisonMetric(
                    metric=metric,
                    baseline_value=float(base.get(metric, 0.0) or 0.0),
                    comparison_value=float(comp.get(metric, 0.0) or 0.0)))
        if not result.metrics:
            result.inconclusive = True
            result.notes.append("no overlapping metrics; inconclusive")
        return result

    def action_vs_perception(self) -> Pilot3ComparisonResult:
        """The central comparison: simulated action vs read-only perception."""
        return self.compare(Pilot3ComparisonArm.READ_ONLY_SENSORY,
                            Pilot3ComparisonArm.GRIDWORLD_SIMULATED_BODY)

    def to_dict(self) -> Dict[str, Any]:
        return {"arms": sorted(self.arms), "arm_count": len(self.arms),
                "metrics_compared": list(COMPARISON_METRICS),
                "real_world_action_evidence": 0}
