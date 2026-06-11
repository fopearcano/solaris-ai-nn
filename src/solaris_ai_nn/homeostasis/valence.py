"""Valence -- feedback polarity, explicitly not emotion.

The estimator folds signed feedback events (reactions, reward/danger,
violations, prediction outcomes, checkpoints, restarts, operator decisions,
energy recovery, blocked actions, Mysterium changes) into a current value, a
rolling value, and a trend, with bounded evidence. Nothing here is happiness
or sadness; it is the running polarity of what the system's feedback loops
reported.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# event kind -> base polarity (events with their own value override this).
EVENT_POLARITY: Dict[str, float] = {
    "reaction": 0.0,              # carries its own valence value
    "reward": 0.6,
    "danger": -0.6,
    "safety_violation": -0.5,
    "prediction_hit": 0.2,
    "prediction_miss": -0.2,
    "checkpoint_ok": 0.15,
    "checkpoint_failed": -0.4,
    "restart_gap": -0.4,
    "operator_approval": 0.3,
    "operator_rejection": -0.3,
    "energy_recovered": 0.2,
    "blocked_action": -0.3,
    "mysterium_drop": 0.1,
    "mysterium_rise": -0.1,
}


@dataclass
class ValenceState:
    """The current feedback-polarity reading."""

    current: float = 0.0
    rolling: float = 0.0
    trend: str = "unknown"
    confidence: float = 0.0
    event_count: int = 0
    note: str = "valence is feedback polarity, not emotion"

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ValenceEstimator:
    """Rolling feedback polarity with attributed evidence."""

    window: int = 50
    _values: List[float] = field(default_factory=list, init=False)
    evidence: List[Dict[str, Any]] = field(default_factory=list, init=False)
    event_count: int = field(default=0, init=False)

    def observe(self, kind: str, value: Optional[float] = None,
                **metadata: Any) -> float:
        """One feedback event; returns the signed polarity recorded."""
        if value is not None:
            polarity = max(-1.0, min(1.0, float(value)))
        else:
            polarity = EVENT_POLARITY.get(kind, 0.0)
        self._values.append(polarity)
        self._values = self._values[-self.window:]
        self.event_count += 1
        self.evidence.append({"kind": kind, "polarity": polarity,
                              "timestamp": time.time(), **metadata})
        self.evidence = self.evidence[-30:]
        return polarity

    def current(self) -> float:
        return round(self._values[-1], 4) if self._values else 0.0

    def rolling(self) -> float:
        if not self._values:
            return 0.0
        return round(sum(self._values) / len(self._values), 4)

    def trend(self) -> str:
        if len(self._values) < 6:
            return "unknown"
        half = len(self._values) // 2
        early = sum(self._values[:half]) / half
        late = sum(self._values[half:]) / (len(self._values) - half)
        if late - early > 0.05:
            return "rising"
        if late - early < -0.05:
            return "falling"
        return "stable"

    def confidence(self) -> float:
        return round(min(0.95, self.event_count / (self.event_count + 5.0)),
                     4)

    def state(self) -> ValenceState:
        return ValenceState(current=self.current(), rolling=self.rolling(),
                            trend=self.trend(),
                            confidence=self.confidence(),
                            event_count=self.event_count)

    def snapshot(self) -> Dict[str, Any]:
        return {**self.state().to_dict(),
                "recent_evidence": self.evidence[-5:]}
