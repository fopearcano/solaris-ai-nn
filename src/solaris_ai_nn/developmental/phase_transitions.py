"""Phase transition detection -- hypotheses with before/after numbers.

Sudden moves in prediction accuracy, Mysterium pressure, graph density,
habit dominance, executive behavior, or homeostatic stability become
*candidates*: each carries the before/after metrics, a confidence, and a
mandatory note that this is a hypothesis about recorded numbers, never
proof of emergence.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

CANDIDATE_NOTE = ("a phase-transition candidate is a hypothesis over "
                  "recorded metrics; it is not proof of emergence")

# (kind, metric, threshold for |delta|, direction or None for both)
_RULES = (
    ("prediction_accuracy_jump", "prediction_accuracy", 0.25, "+"),
    ("prediction_accuracy_drop", "prediction_accuracy", 0.25, "-"),
    ("mysterium_drop", "mysterium_pressure", 0.35, "-"),
    ("mysterium_spike", "mysterium_pressure", 0.35, "+"),
    ("graph_densification", "world_model_edge_density", 1.0, "+"),
    ("habit_dominance_shift", "dominant_habit_weight", 0.5, None),
    ("executive_behavior_shift", "executive_decision_diversity", 0.4,
     None),
    ("homeostatic_stabilization", "homeostatic_tension", 0.3, "-"),
    ("repeated_regression", "regression_count", 2.0, "+"),
    ("restart_recovery", "restart_recovery_count", 1.0, "+"),
)


@dataclass
class PhaseTransitionCandidate:
    """One hypothesis with its before/after evidence."""

    kind: str
    metric: str = ""
    before: float = 0.0
    after: float = 0.0
    delta: float = 0.0
    confidence: float = 0.0
    lifetime_s: float = 0.0
    note: str = CANDIDATE_NOTE
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PhaseTransitionDetector:
    """Compares observation windows; emits candidates, never claims."""

    previous: Dict[str, float] = field(default_factory=dict)
    candidates: List[PhaseTransitionCandidate] = field(
        default_factory=list)
    stagnation_windows: int = field(default=0, init=False)

    def observe(self, metrics: Dict[str, Any],
                lifetime_s: float = 0.0,
                ) -> List[PhaseTransitionCandidate]:
        current = {k: float(v) for k, v in metrics.items()
                   if isinstance(v, (int, float))}
        new: List[PhaseTransitionCandidate] = []
        if self.previous:
            for kind, metric, threshold, direction in _RULES:
                if metric not in current or metric not in self.previous:
                    continue
                before = self.previous[metric]
                after = current[metric]
                delta = after - before
                if direction == "+" and delta < threshold:
                    continue
                if direction == "-" and delta > -threshold:
                    continue
                if direction is None and abs(delta) < threshold:
                    continue
                confidence = round(min(0.8, abs(delta)
                                       / (threshold * 2)), 4)
                new.append(PhaseTransitionCandidate(
                    kind=kind, metric=metric, before=round(before, 6),
                    after=round(after, 6), delta=round(delta, 6),
                    confidence=confidence, lifetime_s=lifetime_s))
            # Long stagnation followed by movement is itself a candidate.
            moved = any(abs(current.get(k, 0.0)
                            - self.previous.get(k, 0.0)) > 1e-9
                        for k in current)
            if not moved:
                self.stagnation_windows += 1
            else:
                if self.stagnation_windows >= 5:
                    new.append(PhaseTransitionCandidate(
                        kind="recovery_after_stagnation",
                        metric="stagnation_windows",
                        before=float(self.stagnation_windows), after=0.0,
                        delta=-float(self.stagnation_windows),
                        confidence=0.5, lifetime_s=lifetime_s))
                self.stagnation_windows = 0
        self.previous = current
        self.candidates.extend(new)
        self.candidates = self.candidates[-100:]
        return new

    def snapshot(self) -> Dict[str, Any]:
        return {
            "candidate_count": len(self.candidates),
            "recent": [c.to_dict() for c in self.candidates[-5:]],
            "stagnation_windows": self.stagnation_windows,
            "note": CANDIDATE_NOTE,
        }
