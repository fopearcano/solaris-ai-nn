"""Developmental time scales -- one clock, seven horizons.

The clock tracks process uptime, cumulative lifetime, active runtime,
gaps, and the maintenance timestamps that long-horizon learning depends
on. It runs in real wall-clock mode for actual long runs and in simulated
mode (with arbitrary acceleration) for tests -- months of developmental
time must never require months of CPU time to test.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


class TimeScale:
    IMMEDIATE = "immediate"  # seconds
    SHORT = "short"          # minutes
    SESSION = "session"      # hours
    DAILY = "daily"          # days
    WEEKLY = "weekly"        # weeks
    MONTHLY = "monthly"      # months
    YEARLY = "yearly"        # years

    ALL = (IMMEDIATE, SHORT, SESSION, DAILY, WEEKLY, MONTHLY, YEARLY)

    SECONDS = {
        IMMEDIATE: 1.0,
        SHORT: 60.0,
        SESSION: 3600.0,
        DAILY: 86400.0,
        WEEKLY: 7 * 86400.0,
        MONTHLY: 30 * 86400.0,
        YEARLY: 365 * 86400.0,
    }


@dataclass
class TimeScaleWindow:
    """One labelled span on one scale."""

    scale: str
    start_s: float
    end_s: float
    label: str = ""

    def duration_s(self) -> float:
        return max(0.0, self.end_s - self.start_s)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "duration_s": self.duration_s()}


@dataclass
class DevelopmentalClock:
    """Lifetime accounting across restarts, simulated or real."""

    simulated: bool = True
    time_acceleration: float = 1.0
    # Persisted lifetime state (restored across restarts).
    cumulative_lifetime_s: float = 0.0
    active_runtime_s: float = 0.0
    paused_gap_s: float = 0.0
    restart_gaps: List[Dict[str, Any]] = field(default_factory=list)
    last_checkpoint_at_s: float = 0.0
    last_consolidation_at_s: float = 0.0
    last_pruning_at_s: float = 0.0
    last_epoch_transition_at_s: float = 0.0
    total_observed_stimuli: int = 0
    total_latent_cycles: int = 0
    total_memory_consolidations: int = 0
    total_world_model_updates: int = 0

    def __post_init__(self) -> None:
        self._process_started = time.time()
        self._last_real_tick = self._process_started

    # -- advancing time ---------------------------------------------------------------

    def advance(self, seconds: float) -> float:
        """Advance simulated time (accelerated); returns the lifetime."""
        delta = max(0.0, float(seconds)) * self.time_acceleration
        self.cumulative_lifetime_s += delta
        self.active_runtime_s += delta
        return self.cumulative_lifetime_s

    def tick_real(self) -> float:
        """Advance by real wall-clock time since the last tick."""
        now = time.time()
        delta = max(0.0, now - self._last_real_tick)
        self._last_real_tick = now
        self.cumulative_lifetime_s += delta
        self.active_runtime_s += delta
        return self.cumulative_lifetime_s

    def note_restart_gap(self, gap_s: float, reason: str = "") -> None:
        gap_s = max(0.0, float(gap_s))
        self.paused_gap_s += gap_s
        self.cumulative_lifetime_s += gap_s  # the gap is lived time too
        self.restart_gaps.append({"gap_s": gap_s, "reason": reason,
                                  "at_lifetime_s":
                                      self.cumulative_lifetime_s})
        self.restart_gaps = self.restart_gaps[-50:]

    # -- maintenance markers ------------------------------------------------------------

    def note_checkpoint(self) -> None:
        self.last_checkpoint_at_s = self.cumulative_lifetime_s

    def note_consolidation(self) -> None:
        self.last_consolidation_at_s = self.cumulative_lifetime_s
        self.total_memory_consolidations += 1

    def note_pruning(self) -> None:
        self.last_pruning_at_s = self.cumulative_lifetime_s

    def note_epoch_transition(self) -> None:
        self.last_epoch_transition_at_s = self.cumulative_lifetime_s

    # -- views --------------------------------------------------------------------

    def process_uptime_s(self) -> float:
        return time.time() - self._process_started

    def checkpoint_age_s(self) -> float:
        return max(0.0, self.cumulative_lifetime_s
                   - self.last_checkpoint_at_s)

    def age_in(self, scale: str) -> float:
        """Lifetime expressed in units of one scale."""
        return self.cumulative_lifetime_s / TimeScale.SECONDS[scale]

    def active_runtime_ratio(self) -> float:
        total = self.cumulative_lifetime_s
        return round(self.active_runtime_s / total, 4) if total else 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulated": self.simulated,
            "time_acceleration": self.time_acceleration,
            "process_uptime_s": round(self.process_uptime_s(), 3),
            "cumulative_lifetime_s": round(self.cumulative_lifetime_s, 3),
            "active_runtime_s": round(self.active_runtime_s, 3),
            "active_runtime_ratio": self.active_runtime_ratio(),
            "paused_gap_s": round(self.paused_gap_s, 3),
            "restart_gap_count": len(self.restart_gaps),
            "restart_gaps_tail": self.restart_gaps[-5:],
            "checkpoint_age_s": round(self.checkpoint_age_s(), 3),
            "last_consolidation_at_s": self.last_consolidation_at_s,
            "last_pruning_at_s": self.last_pruning_at_s,
            "last_epoch_transition_at_s":
                self.last_epoch_transition_at_s,
            "total_observed_stimuli": self.total_observed_stimuli,
            "total_latent_cycles": self.total_latent_cycles,
            "total_memory_consolidations":
                self.total_memory_consolidations,
            "total_world_model_updates": self.total_world_model_updates,
            "age": {scale: round(self.age_in(scale), 4)
                    for scale in TimeScale.ALL},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DevelopmentalClock":
        clock = cls(simulated=bool(data.get("simulated", True)),
                    time_acceleration=float(
                        data.get("time_acceleration", 1.0)))
        clock.cumulative_lifetime_s = float(
            data.get("cumulative_lifetime_s", 0.0))
        clock.active_runtime_s = float(data.get("active_runtime_s", 0.0))
        clock.paused_gap_s = float(data.get("paused_gap_s", 0.0))
        clock.restart_gaps = list(data.get("restart_gaps_tail", []))
        clock.last_checkpoint_at_s = float(
            data.get("checkpoint_age_s", 0.0)
            and clock.cumulative_lifetime_s
            - float(data.get("checkpoint_age_s", 0.0)))
        clock.last_consolidation_at_s = float(
            data.get("last_consolidation_at_s", 0.0))
        clock.last_pruning_at_s = float(data.get("last_pruning_at_s",
                                                 0.0))
        clock.last_epoch_transition_at_s = float(
            data.get("last_epoch_transition_at_s", 0.0))
        clock.total_observed_stimuli = int(
            data.get("total_observed_stimuli", 0))
        clock.total_latent_cycles = int(data.get("total_latent_cycles",
                                                 0))
        clock.total_memory_consolidations = int(
            data.get("total_memory_consolidations", 0))
        clock.total_world_model_updates = int(
            data.get("total_world_model_updates", 0))
        return clock
