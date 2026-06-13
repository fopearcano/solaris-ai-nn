"""Deprivation / silence -- long low-input windows, bounded.

Short silences, long silences, sensory monotony, post-anomaly quiet:
windows where little or nothing arrives. The model decides whether the
current step is deprived and emits absence-shaped stimuli, while a hard
``max_window`` keeps any single silence from running forever (a test of
latent activation, never a way to starve the system into a crash).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DeprivationKind:
    SHORT_SILENCE = "short_silence"
    LONG_SILENCE = "long_silence"
    SENSORY_MONOTONY = "sensory_monotony"
    REPEATED_SAME = "repeated_same_stimulus"
    ABSENCE_AFTER_EXPECTATION = "absence_after_expectation"
    POST_ANOMALY_QUIET = "post_anomaly_quiet"

    ALL = (SHORT_SILENCE, LONG_SILENCE, SENSORY_MONOTONY,
           REPEATED_SAME, ABSENCE_AFTER_EXPECTATION,
           POST_ANOMALY_QUIET)


@dataclass
class DeprivationModel:
    """Bounded silence/monotony windows."""

    rng: Any = None
    max_window: int = 30  # hard cap on a single deprivation window
    short_window: int = 5
    long_window: int = 20
    _active_kind: Optional[str] = field(default=None, init=False)
    _remaining: int = field(default=0, init=False)
    windows: List[Dict[str, Any]] = field(default_factory=list)
    deprived_steps: int = field(default=0, init=False)

    def maybe_start(self, step: int, silence_probability: float,
                    after_anomaly: bool = False) -> Optional[str]:
        """Begin a deprivation window with the given probability."""
        if self._remaining > 0:
            return self._active_kind
        if after_anomaly:
            kind, length = (DeprivationKind.POST_ANOMALY_QUIET,
                            self.short_window)
        elif self.rng is not None and self.rng.random() \
                < max(0.0, min(1.0, silence_probability)):
            roll = self.rng.random()
            if roll < 0.5:
                kind, length = (DeprivationKind.SHORT_SILENCE,
                                self.short_window)
            elif roll < 0.8:
                kind, length = (DeprivationKind.LONG_SILENCE,
                                self.long_window)
            else:
                kind, length = (DeprivationKind.SENSORY_MONOTONY,
                                self.short_window)
        else:
            return None
        self._active_kind = kind
        self._remaining = min(length, self.max_window)
        self.windows.append({"step": step, "kind": kind,
                             "length": self._remaining})
        self.windows = self.windows[-100:]
        return kind

    def step_window(self) -> Optional[str]:
        """Advance an active window; returns its kind while it lasts."""
        if self._remaining <= 0:
            self._active_kind = None
            return None
        self._remaining -= 1
        self.deprived_steps += 1
        kind = self._active_kind
        if self._remaining <= 0:
            self._active_kind = None
        return kind

    @property
    def active(self) -> bool:
        return self._remaining > 0

    def snapshot(self) -> Dict[str, Any]:
        return {
            "window_count": len(self.windows),
            "deprived_steps": self.deprived_steps,
            "max_window": self.max_window,
            "active": self.active,
            "recent": self.windows[-5:],
            "note": "deprivation windows are bounded; they test latent "
                    "activation and absence-symbol emergence",
        }
