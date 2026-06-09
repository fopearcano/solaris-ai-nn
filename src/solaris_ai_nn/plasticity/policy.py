"""PlasticityPolicy -- simple, explicit rules that *propose* mutations.

The policy reads a context dict (telemetry, prediction error, Logos state, habit
stats, drift, continuity) and proposes plasticity steps. It does not apply
anything and it does not validate -- the engine does both. The rules are
deliberately explicit and bounded; there is **no** black-box meta-learning here.

Rule summary (section 5):
    A. high error (streak)        -> raise learning rate
    B. stable low error           -> lower learning rate + raise stabilization
    C. repeatedly-reinforced habit-> raise that habit's bias weight
    D. unused pathways present     -> raise synthesis pruning threshold
    E. high Logos fracture         -> raise exploration
    F. division dominates, low err -> raise stabilization
    G. absence cycles dominate     -> lower exploration (reduce overreaction)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .mutation import (
    BRIDGE,
    HABIT,
    READOUT,
    SYNTHESIS,
    PlasticityChange,
    PlasticityStep,
    PlasticityTarget,
)
from .safety import SAFE_BOUNDS
from ..utils.math import clamp


def _bounds(component: str, parameter: str, default=(0.0, 1.0)):
    return SAFE_BOUNDS.get((component, parameter), default)


@dataclass
class PlasticityPolicy:
    """Threshold-based proposer of bounded plasticity steps."""

    error_high: float = 0.7
    error_low: float = 0.25
    high_streak_needed: int = 3
    low_streak_needed: int = 3
    lr_up_factor: float = 1.15
    lr_down_factor: float = 0.9
    habit_reinforce_count: int = 5
    habit_weight_delta: float = 0.1
    fracture_high: float = 0.5
    explore_delta: float = 0.05
    stabilize_delta: float = 0.05
    prune_threshold_delta: float = 0.005
    absence_ratio_high: float = 0.5

    def _mk(self, ctx: Dict[str, Any], component: str, parameter: str,
            old: Any, new: Any, reason: str, expected: str, trigger: str) -> PlasticityStep:
        return PlasticityStep(
            target=PlasticityTarget(component, parameter),
            change=PlasticityChange(old_value=old, new_value=new, expected_effect=expected),
            reason=reason,
            trigger_source=trigger,
            run_id=ctx.get("run_id", ""),
            session_id=ctx.get("session_id", ""),
            lifetime_step=ctx.get("lifetime_step", 0),
        )

    def propose(self, ctx: Dict[str, Any]) -> List[PlasticityStep]:
        steps: List[PlasticityStep] = []
        cur: Dict[str, Any] = ctx.get("current", {})

        recent_error = float(ctx.get("recent_error", 0.0))
        high_streak = int(ctx.get("error_high_streak", 0))
        low_streak = int(ctx.get("error_low_streak", 0))
        fracture = float(ctx.get("logos_fracture", 0.0))
        division = float(ctx.get("logos_division", 0.0))
        union = float(ctx.get("logos_union", 0.0))
        absence_ratio = float(ctx.get("absence_ratio", 0.0))
        positive = int(ctx.get("positive_reactions", 0))

        # A. Persistent high error -> raise learning rate.
        if high_streak >= self.high_streak_needed:
            lo, hi = _bounds(READOUT, "learning_rate")
            old = float(cur.get("readout.learning_rate", 0.0))
            new = clamp(old * self.lr_up_factor, lo, hi)
            if new > old:
                steps.append(self._mk(ctx, READOUT, "learning_rate", old, new,
                    f"prediction error high for {high_streak} steps",
                    "faster adaptation", "policy:high_error"))

        # B. Stable low error -> lower learning rate + raise stabilization.
        if low_streak >= self.low_streak_needed:
            lo, hi = _bounds(READOUT, "learning_rate")
            old = float(cur.get("readout.learning_rate", 0.0))
            new = clamp(old * self.lr_down_factor, lo, hi)
            if new < old:
                steps.append(self._mk(ctx, READOUT, "learning_rate", old, new,
                    f"prediction error low/stable for {low_streak} steps",
                    "steadier learning", "policy:low_error"))
            slo, shi = _bounds(BRIDGE, "stabilization_tendency")
            sold = float(cur.get("bridge.stabilization_tendency", 0.0))
            snew = clamp(sold + self.stabilize_delta, slo, shi)
            if snew > sold:
                steps.append(self._mk(ctx, BRIDGE, "stabilization_tendency", sold, snew,
                    "low stable error favours stabilization",
                    "less churn", "policy:low_error"))

        # C. Repeatedly-reinforced habit -> raise that habit's bias weight.
        habit = ctx.get("strongest_habit")
        if habit and int(habit.get("count", 0)) >= self.habit_reinforce_count:
            max_w = float(cur.get("habit.max_habit_weight", 1.0))
            old = float(habit.get("weight", 0.0))
            sign = 1.0 if old >= 0 else -1.0
            new = clamp(old + sign * self.habit_weight_delta, -max_w, max_w)
            if abs(new) > abs(old):
                param = f"weight:{habit['pattern']}|{habit['action']}"
                steps.append(self._mk(ctx, HABIT, param, old, new,
                    f"habit reinforced {habit['count']}x",
                    "strengthen rewarded pathway", "policy:habit"))

        # D. Unused pathways present -> raise synthesis pruning threshold.
        unused = int(ctx.get("unused_pathways", 0))
        if unused > 0 and "synthesis.pruning_threshold" in cur:
            lo, hi = _bounds(SYNTHESIS, "pruning_threshold")
            old = float(cur.get("synthesis.pruning_threshold", 0.0))
            new = clamp(old + self.prune_threshold_delta, lo, hi)
            if new > old:
                steps.append(self._mk(ctx, SYNTHESIS, "pruning_threshold", old, new,
                    f"{unused} unused readout pathways",
                    "subtract weak pathways", "policy:unused"))

        # E. High Logos fracture -> raise exploration.
        if fracture >= self.fracture_high:
            lo, hi = _bounds(BRIDGE, "exploration_tendency")
            old = float(cur.get("bridge.exploration_tendency", 0.0))
            new = clamp(old + self.explore_delta, lo, hi)
            if new > old:
                steps.append(self._mk(ctx, BRIDGE, "exploration_tendency", old, new,
                    f"Logos fracture high ({fracture:.2f})",
                    "explore more under conflict", "policy:fracture"))

        # F. Division dominates and error low -> raise stabilization.
        if division > union and recent_error <= self.error_low:
            lo, hi = _bounds(BRIDGE, "stabilization_tendency")
            old = float(cur.get("bridge.stabilization_tendency", 0.0))
            new = clamp(old + self.stabilize_delta, lo, hi)
            if new > old and not any(s.target.parameter == "stabilization_tendency" for s in steps):
                steps.append(self._mk(ctx, BRIDGE, "stabilization_tendency", old, new,
                    "rational (division) dominates with low error",
                    "consolidate confident behaviour", "policy:division"))

        # G. Absence cycles dominate (and not rewarded) -> lower exploration.
        if absence_ratio >= self.absence_ratio_high and positive == 0:
            lo, hi = _bounds(BRIDGE, "exploration_tendency")
            old = float(cur.get("bridge.exploration_tendency", 0.0))
            new = clamp(old - self.explore_delta, lo, hi)
            if new < old and not any(s.target.parameter == "exploration_tendency" for s in steps):
                steps.append(self._mk(ctx, BRIDGE, "exploration_tendency", old, new,
                    f"absence cycles dominate ({absence_ratio:.2f}), unrewarded",
                    "reduce overreaction to absence", "policy:absence"))

        return steps
