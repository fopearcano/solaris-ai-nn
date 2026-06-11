"""Developmental epochs -- labels over metrics, never proof of anything.

Nine epochs from bootstrapping to mature soak (plus the honest
``uncertain_regression``). Transitions depend on measured signals --
runtime, memory volume, habit stability, world-model growth, prediction
trends, Mysterium trends, restart stability -- not on dates alone. Every
transition is logged, reversible, and explicitly a label: an epoch name
describes recorded metrics, it proves nothing about consciousness.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

EPOCH_NOTE = ("an epoch is a label over recorded metrics, reversible and "
              "uncertain -- not proof of development, emergence, or "
              "consciousness")


class DevelopmentalEpoch:
    BOOTSTRAPPING = "bootstrapping"
    EARLY_EXPOSURE = "early_exposure"
    HABIT_FORMATION = "habit_formation"
    WORLD_MODEL_GROWTH = "world_model_growth"
    CONSOLIDATION_DOMINANT = "consolidation_dominant"
    LONG_RUN_STABILIZATION = "long_run_stabilization"
    DRIFT_OBSERVATION = "drift_observation"
    MATURE_SOAK = "mature_soak"
    UNCERTAIN_REGRESSION = "uncertain_regression"

    ALL = (BOOTSTRAPPING, EARLY_EXPOSURE, HABIT_FORMATION,
           WORLD_MODEL_GROWTH, CONSOLIDATION_DOMINANT,
           LONG_RUN_STABILIZATION, DRIFT_OBSERVATION, MATURE_SOAK,
           UNCERTAIN_REGRESSION)

    ORDER = (BOOTSTRAPPING, EARLY_EXPOSURE, HABIT_FORMATION,
             WORLD_MODEL_GROWTH, CONSOLIDATION_DOMINANT,
             LONG_RUN_STABILIZATION, DRIFT_OBSERVATION, MATURE_SOAK)


@dataclass
class EpochTransition:
    """One logged transition with the signals that justified it."""

    from_epoch: str
    to_epoch: str
    reason: str = ""
    signals: Dict[str, Any] = field(default_factory=dict)
    uncertain: bool = False
    lifetime_s: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class EpochState:
    """Where the runtime currently sits, with its full history."""

    current: str = DevelopmentalEpoch.BOOTSTRAPPING
    entered_at_lifetime_s: float = 0.0
    previous: str = ""
    transitions: List[EpochTransition] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current": self.current,
            "entered_at_lifetime_s": self.entered_at_lifetime_s,
            "previous": self.previous,
            "transition_count": len(self.transitions),
            "history": [t.to_dict() for t in self.transitions[-10:]],
            "note": EPOCH_NOTE,
        }


# Forward ladder: (target epoch, signal predicate description, predicate).
_FORWARD_RULES = (
    (DevelopmentalEpoch.EARLY_EXPOSURE,
     "total stimuli >= 50",
     lambda s: s.get("total_observed_stimuli", 0) >= 50),
    (DevelopmentalEpoch.HABIT_FORMATION,
     "stable habits >= 3",
     lambda s: s.get("stable_habit_count", 0) >= 3),
    (DevelopmentalEpoch.WORLD_MODEL_GROWTH,
     "world-model nodes >= 20",
     lambda s: s.get("world_model_node_count", 0) >= 20),
    (DevelopmentalEpoch.CONSOLIDATION_DOMINANT,
     "memory consolidations >= 3",
     lambda s: s.get("consolidation_count", 0) >= 3),
    (DevelopmentalEpoch.LONG_RUN_STABILIZATION,
     "runtime >= 24h and non-negative prediction trend",
     lambda s: s.get("runtime_hours", 0.0) >= 24.0
     and s.get("prediction_accuracy_trend", 0.0) >= -0.05),
    (DevelopmentalEpoch.DRIFT_OBSERVATION,
     "runtime >= 1 week and pruning stable",
     lambda s: s.get("runtime_hours", 0.0) >= 24.0 * 7
     and s.get("pruning_stability", 1.0) >= 0.5),
    (DevelopmentalEpoch.MATURE_SOAK,
     "runtime >= 1 month and restart stability >= 0.7",
     lambda s: s.get("runtime_hours", 0.0) >= 24.0 * 30
     and s.get("restart_stability", 1.0) >= 0.7),
)


def _regressing(signals: Dict[str, Any]) -> Optional[str]:
    if signals.get("prediction_accuracy_trend", 0.0) < -0.25:
        return "prediction accuracy is falling sharply"
    if signals.get("boundary_violation_count", 0) >= 3:
        return "repeated boundary violations"
    if signals.get("restart_stability", 1.0) < 0.4:
        return "restart stability collapsed"
    if signals.get("no_safe_action_rate", 0.0) > 0.5:
        return "the executive repeatedly finds no safe action"
    if signals.get("homeostatic_stability", 1.0) < 0.3:
        return "homeostatic variables are unstable"
    return None


@dataclass
class EpochManager:
    """Evaluates signals; transitions are logged and reversible."""

    state: EpochState = field(default_factory=EpochState)

    def evaluate(self, signals: Dict[str, Any],
                 lifetime_s: float = 0.0) -> Optional[EpochTransition]:
        """One evaluation pass; returns the transition if one fired."""
        current = self.state.current
        regression = _regressing(signals)
        if regression and current \
                != DevelopmentalEpoch.UNCERTAIN_REGRESSION:
            return self._transition(
                DevelopmentalEpoch.UNCERTAIN_REGRESSION,
                f"regression signal: {regression}", signals, lifetime_s,
                uncertain=True)
        if current == DevelopmentalEpoch.UNCERTAIN_REGRESSION:
            if regression is None:
                # Recovered: return to the last forward epoch (or start).
                target = (self.state.previous
                          if self.state.previous in DevelopmentalEpoch.ORDER
                          else DevelopmentalEpoch.BOOTSTRAPPING)
                return self._transition(
                    target, "regression signals cleared; the previous "
                            "epoch label is restored (uncertainly)",
                    signals, lifetime_s, uncertain=True)
            return None
        # Forward ladder: take the next rung whose predicate holds.
        index = DevelopmentalEpoch.ORDER.index(current)
        for target, description, predicate in _FORWARD_RULES:
            target_index = DevelopmentalEpoch.ORDER.index(target)
            if target_index == index + 1 and predicate(signals):
                return self._transition(target, description, signals,
                                        lifetime_s)
        return None

    def _transition(self, to_epoch: str, reason: str,
                    signals: Dict[str, Any], lifetime_s: float,
                    uncertain: bool = False) -> EpochTransition:
        transition = EpochTransition(
            from_epoch=self.state.current, to_epoch=to_epoch,
            reason=reason, uncertain=uncertain,
            lifetime_s=lifetime_s,
            signals={k: signals.get(k) for k in
                     ("runtime_hours", "total_observed_stimuli",
                      "stable_habit_count", "world_model_node_count",
                      "consolidation_count",
                      "prediction_accuracy_trend",
                      "mysterium_trend", "restart_stability",
                      "boundary_violation_count")
                     if k in signals})
        self.state.previous = self.state.current
        self.state.current = to_epoch
        self.state.entered_at_lifetime_s = lifetime_s
        self.state.transitions.append(transition)
        self.state.transitions = self.state.transitions[-100:]
        return transition

    def snapshot(self) -> Dict[str, Any]:
        return self.state.to_dict()
