"""Telemetry -- the observable health of a long-running experiment.

Every philosophical claim in this project must reduce to a number you can watch.
Telemetry is where those numbers live: counts of steps and events, how often the
substrate updated, how prediction error trends, how much habit mass exists, how
much synthesis has subtracted, and wall-clock duration.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Telemetry:
    """Mutable counters and rolling stats for one experiment run."""

    steps: int = 0
    heartbeats: int = 0
    events: int = 0
    reservoir_updates: int = 0
    readout_updates: int = 0
    pruning_passes: int = 0
    pruned_pathways: int = 0
    memory_trace_length: int = 0

    _error_sum: float = 0.0
    _error_count: int = 0
    _error_window: List[float] = field(default_factory=list, repr=False)
    _window_size: int = 100

    habit_total_weight: float = 0.0
    habit_weight_change: float = 0.0
    _last_habit_weight: float = 0.0

    start_time: float = field(default_factory=time.perf_counter)
    duration: float = 0.0

    # -- recording ----------------------------------------------------------

    def tick(self) -> None:
        self.steps += 1

    def heartbeat(self) -> None:
        self.heartbeats += 1

    def event(self) -> None:
        self.events += 1

    def reservoir_update(self) -> None:
        self.reservoir_updates += 1

    def readout_update(self, error: float) -> None:
        self.readout_updates += 1
        self._error_sum += abs(error)
        self._error_count += 1
        self._error_window.append(abs(error))
        if len(self._error_window) > self._window_size:
            self._error_window.pop(0)

    def pruning(self, removed: int) -> None:
        self.pruning_passes += 1
        self.pruned_pathways += removed

    def update_habit(self, total_weight: float) -> None:
        self.habit_weight_change = total_weight - self._last_habit_weight
        self._last_habit_weight = total_weight
        self.habit_total_weight = total_weight

    def set_trace_length(self, length: int) -> None:
        self.memory_trace_length = length

    def finish(self) -> None:
        self.duration = time.perf_counter() - self.start_time

    # -- derived stats ------------------------------------------------------

    @property
    def average_prediction_error(self) -> float:
        """Mean |prediction error| over all readout updates."""
        if self._error_count == 0:
            return 0.0
        return self._error_sum / self._error_count

    @property
    def recent_prediction_error(self) -> float:
        """Mean |error| over the most recent window (shows the learning trend)."""
        if not self._error_window:
            return 0.0
        return sum(self._error_window) / len(self._error_window)

    def report(self) -> Dict[str, Any]:
        """A flat dict of all metrics, suitable for logging or JSON."""
        return {
            "steps": self.steps,
            "heartbeats": self.heartbeats,
            "events": self.events,
            "reservoir_updates": self.reservoir_updates,
            "readout_updates": self.readout_updates,
            "average_prediction_error": round(self.average_prediction_error, 6),
            "recent_prediction_error": round(self.recent_prediction_error, 6),
            "habit_total_weight": round(self.habit_total_weight, 6),
            "habit_weight_change": round(self.habit_weight_change, 6),
            "pruning_passes": self.pruning_passes,
            "pruned_pathways": self.pruned_pathways,
            "memory_trace_length": self.memory_trace_length,
            "duration_seconds": round(self.duration, 6),
        }

    def __str__(self) -> str:
        lines = ["Telemetry:"]
        for key, value in self.report().items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)
