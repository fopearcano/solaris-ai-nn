"""Regimes -- stimulus ecologies, not lesson plans.

Each regime is a probability profile over what the world tends to emit:
how often a signal arrives at all, how much it repeats, how novel or
anomalous it is, whether danger/reward analogues and delayed consequences
appear. No regime supplies a correct answer; it supplies a *pressure*.
Regime changes are logged so reports can show what world the system
actually inhabited.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RegimeType:
    STABLE_REPETITION = "stable_repetition"
    SPARSE_DESERT = "sparse_desert"
    NOISY_ENVIRONMENT = "noisy_environment"
    NOVELTY_BURST = "novelty_burst"
    DANGER_REWARD_FIELD = "danger_reward_field"
    BOUNDARY_MAZE = "boundary_maze"
    LONG_SILENCE = "long_silence"
    DELAYED_FEEDBACK_WORLD = "delayed_feedback_world"
    SEASONAL_DRIFT = "seasonal_drift"
    MIXED_NURSERY = "mixed_nursery"

    ALL = (STABLE_REPETITION, SPARSE_DESERT, NOISY_ENVIRONMENT,
           NOVELTY_BURST, DANGER_REWARD_FIELD, BOUNDARY_MAZE,
           LONG_SILENCE, DELAYED_FEEDBACK_WORLD, SEASONAL_DRIFT,
           MIXED_NURSERY)


@dataclass
class EcologyRegime:
    """One stimulus ecology's probability profile."""

    name: str
    silence_probability: float = 0.2
    pattern_recurrence: float = 0.5
    novelty_probability: float = 0.05
    anomaly_probability: float = 0.02
    delayed_consequence_probability: float = 0.05
    boundary_probability: float = 0.05
    danger_probability: float = 0.05
    reward_probability: float = 0.1
    expected_pressure: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


_REGIMES: Dict[str, EcologyRegime] = {
    RegimeType.STABLE_REPETITION: EcologyRegime(
        name=RegimeType.STABLE_REPETITION, silence_probability=0.15,
        pattern_recurrence=0.85, novelty_probability=0.02,
        anomaly_probability=0.01, reward_probability=0.12,
        expected_pressure="habit formation and stable proto-symbols"),
    RegimeType.SPARSE_DESERT: EcologyRegime(
        name=RegimeType.SPARSE_DESERT, silence_probability=0.6,
        pattern_recurrence=0.4, novelty_probability=0.03,
        reward_probability=0.04,
        expected_pressure="seek-signal need and absence symbols"),
    RegimeType.NOISY_ENVIRONMENT: EcologyRegime(
        name=RegimeType.NOISY_ENVIRONMENT, silence_probability=0.05,
        pattern_recurrence=0.3, novelty_probability=0.15,
        anomaly_probability=0.08,
        expected_pressure="noise tolerance and pattern extraction"),
    RegimeType.NOVELTY_BURST: EcologyRegime(
        name=RegimeType.NOVELTY_BURST, silence_probability=0.1,
        pattern_recurrence=0.4, novelty_probability=0.3,
        anomaly_probability=0.05,
        expected_pressure="Mysterium regulation and novel-symbol birth"),
    RegimeType.DANGER_REWARD_FIELD: EcologyRegime(
        name=RegimeType.DANGER_REWARD_FIELD, silence_probability=0.15,
        pattern_recurrence=0.6, danger_probability=0.2,
        reward_probability=0.2, boundary_probability=0.1,
        expected_pressure="valence learning and safety pressure"),
    RegimeType.BOUNDARY_MAZE: EcologyRegime(
        name=RegimeType.BOUNDARY_MAZE, silence_probability=0.15,
        pattern_recurrence=0.5, boundary_probability=0.3,
        danger_probability=0.1,
        expected_pressure="boundary patterns and inhibition"),
    RegimeType.LONG_SILENCE: EcologyRegime(
        name=RegimeType.LONG_SILENCE, silence_probability=0.8,
        pattern_recurrence=0.5, novelty_probability=0.02,
        expected_pressure="latent activation and absence symbols"),
    RegimeType.DELAYED_FEEDBACK_WORLD: EcologyRegime(
        name=RegimeType.DELAYED_FEEDBACK_WORLD, silence_probability=0.2,
        pattern_recurrence=0.6, delayed_consequence_probability=0.25,
        reward_probability=0.1,
        expected_pressure="cross-time association in the world model"),
    RegimeType.SEASONAL_DRIFT: EcologyRegime(
        name=RegimeType.SEASONAL_DRIFT, silence_probability=0.25,
        pattern_recurrence=0.6, novelty_probability=0.08,
        anomaly_probability=0.03,
        expected_pressure="long-horizon adaptation to drift"),
    RegimeType.MIXED_NURSERY: EcologyRegime(
        name=RegimeType.MIXED_NURSERY, silence_probability=0.25,
        pattern_recurrence=0.6, novelty_probability=0.08,
        anomaly_probability=0.04, delayed_consequence_probability=0.08,
        boundary_probability=0.06, danger_probability=0.06,
        reward_probability=0.12,
        expected_pressure="balanced exposure across all pressures"),
}


def get_regime(name: str) -> EcologyRegime:
    if name not in _REGIMES:
        raise ValueError(f"unknown regime {name!r}")
    return _REGIMES[name]


@dataclass
class RegimeManager:
    """Holds the active regimes and logs every change."""

    active_regimes: List[str] = field(
        default_factory=lambda: [RegimeType.MIXED_NURSERY])
    history: List[Dict[str, Any]] = field(default_factory=list)
    current: str = field(default="", init=False)
    changes: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if not self.active_regimes:
            self.active_regimes = [RegimeType.MIXED_NURSERY]
        for name in self.active_regimes:
            get_regime(name)  # validate
        self.current = self.active_regimes[0]
        self.history.append({"step": 0, "regime": self.current,
                             "reason": "initial"})

    def set_regime(self, name: str, step: int = 0,
                   reason: str = "") -> EcologyRegime:
        regime = get_regime(name)
        if name != self.current:
            self.changes += 1
            self.history.append({"step": step, "regime": name,
                                 "from": self.current,
                                 "reason": reason or "regime change",
                                 "timestamp": time.time()})
            self.history = self.history[-200:]
            self.current = name
        return regime

    def current_regime(self) -> EcologyRegime:
        return get_regime(self.current)

    def snapshot(self) -> Dict[str, Any]:
        regime = self.current_regime()
        return {
            "active_regimes": list(self.active_regimes),
            "current": self.current,
            "expected_pressure": regime.expected_pressure,
            "regime_changes": self.changes,
            "profile": regime.to_dict(),
            "recent_changes": self.history[-5:],
        }
