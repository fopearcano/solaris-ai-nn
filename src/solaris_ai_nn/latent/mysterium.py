"""MysteriumTracker -- unknown pressure as a number with receipts.

"Mysterium" is Solaris_Ai's name for the pull of the unknown. Here it is
strictly a numeric estimate in [0, 1] of how much the system currently fails
to predict or explain its own inputs -- nothing mystical. It rises with
novelty, prediction misses, unexplained error, Logos fracture, blocked
actions, poor trace coverage, counterfactual divergence, and replay
mismatches; it falls with successful prediction, stable patterns,
consolidation, and reproduced replays. Every change carries its reason.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# (context key, threshold-ish extractor) -> (reason, delta). Tuned small so
# pressure moves smoothly, not in jumps.
INCREASE_RULES = (
    ("novelty", 0.5, "high novelty in recent input", 0.04),
    ("prediction_miss_streak", 3, "repeated prediction misses", 0.05),
    ("unexplained_error", 0.5, "high unexplained prediction error", 0.04),
    ("logos_fracture", 0.5, "high Logos fracture", 0.03),
    ("blocked_actions", 1, "actions were blocked by safety", 0.03),
    ("low_trace_coverage", True, "explanations cover little of the trace",
     0.03),
    ("counterfactual_divergence", 0.5,
     "counterfactual replay diverged strongly", 0.04),
    ("replay_mismatch", True, "replay failed to reproduce recorded behaviour",
     0.06),
)

DECREASE_RULES = (
    ("prediction_hit", True, "successful prediction", 0.03),
    ("stable_patterns", True, "stable repeated patterns observed", 0.02),
    ("consolidated", True, "memory was consolidated", 0.04),
    ("reduced_error", True, "unexplained error decreased", 0.02),
    ("replay_reproduced", True, "replay reproduced recorded behaviour", 0.03),
)


@dataclass
class MysteriumState:
    """The current unknown-pressure reading."""

    pressure: float
    level: str
    trend: str
    top_reasons: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class MysteriumTracker:
    """Numeric unknown-pressure estimate with attributed changes."""

    pressure: float = 0.2
    max_reasons: int = 100
    reasons: List[Dict[str, Any]] = field(default_factory=list, init=False)
    _history: List[float] = field(default_factory=list, init=False)

    def _clamp(self) -> None:
        self.pressure = max(0.0, min(1.0, self.pressure))

    def increase(self, reason: str, amount: float) -> float:
        amount = abs(float(amount))
        self.pressure += amount
        self._clamp()
        self.reasons.append({"reason": reason, "delta": +amount,
                             "pressure": round(self.pressure, 4),
                             "timestamp": time.time()})
        self.reasons = self.reasons[-self.max_reasons:]
        return self.pressure

    def decrease(self, reason: str, amount: float) -> float:
        amount = abs(float(amount))
        self.pressure -= amount
        self._clamp()
        self.reasons.append({"reason": reason, "delta": -amount,
                             "pressure": round(self.pressure, 4),
                             "timestamp": time.time()})
        self.reasons = self.reasons[-self.max_reasons:]
        return self.pressure

    def update(self, context: Optional[Dict[str, Any]] = None,
               ) -> MysteriumState:
        """Apply the rule table to a context snapshot; returns the state."""
        ctx = context or {}
        for key, threshold, reason, delta in INCREASE_RULES:
            value = ctx.get(key)
            if value is None:
                continue
            if isinstance(threshold, bool):
                if bool(value):
                    self.increase(reason, delta)
            elif isinstance(value, (int, float)) and value >= threshold:
                self.increase(reason, delta)
        for key, threshold, reason, delta in DECREASE_RULES:
            value = ctx.get(key)
            if value is None:
                continue
            if bool(value):
                self.decrease(reason, delta)
        self._history.append(self.pressure)
        self._history = self._history[-200:]
        return self.state()

    # -- readings ------------------------------------------------------------------

    def level(self) -> str:
        if self.pressure >= 0.7:
            return "high"
        if self.pressure >= 0.4:
            return "elevated"
        return "low"

    def trend(self) -> str:
        if len(self._history) < 4:
            return "stable"
        delta = self._history[-1] - self._history[-4]
        if delta > 0.02:
            return "rising"
        if delta < -0.02:
            return "falling"
        return "stable"

    def state(self) -> MysteriumState:
        return MysteriumState(
            pressure=round(self.pressure, 4), level=self.level(),
            trend=self.trend(), top_reasons=self.reasons[-5:])

    def snapshot(self) -> Dict[str, Any]:
        return {
            "pressure": round(self.pressure, 4),
            "level": self.level(),
            "trend": self.trend(),
            "recent_reasons": self.reasons[-8:],
            "history_tail": [round(p, 4) for p in self._history[-10:]],
            "note": "a numeric unknown-pressure estimate; nothing mystical",
        }
