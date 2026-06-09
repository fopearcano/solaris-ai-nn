"""Telemetry -- the observable health of a long-running experiment.

Every philosophical claim in this project must reduce to a number you can watch.
Telemetry is where those numbers live: counts of steps and events, how often the
substrate updated, how prediction error trends, how much habit mass exists, how
much synthesis has subtracted, and wall-clock duration.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Union


@dataclass
class Telemetry:
    """Mutable counters and rolling stats for one experiment run.

    Counters split into *session* scope (this process run) and *lifetime* scope
    (accumulated across restarts; set by the runner from the manifest).
    """

    steps: int = 0
    heartbeats: int = 0
    events: int = 0
    reservoir_updates: int = 0
    readout_updates: int = 0
    pruning_passes: int = 0
    pruned_pathways: int = 0
    memory_trace_length: int = 0

    # Continuity / lifetime metrics (Phase 2).
    lifetime_steps: int = 0
    checkpoints: int = 0
    restarts: int = 0
    unexpected_deaths: int = 0
    brain_death_gap_seconds: float = 0.0
    reservoir_norm: float = 0.0
    habit_reinforcements: int = 0
    trace_event_count: int = 0

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
        self.trace_event_count = length

    # -- continuity recording ----------------------------------------------

    def checkpoint(self) -> None:
        self.checkpoints += 1

    def record_reinforcement(self) -> None:
        self.habit_reinforcements += 1

    def set_lifetime_steps(self, lifetime_steps: int) -> None:
        self.lifetime_steps = lifetime_steps

    def set_restarts(self, restarts: int) -> None:
        self.restarts = restarts

    def record_unexpected_death(self, gap_seconds: float = 0.0) -> None:
        self.unexpected_deaths += 1
        self.brain_death_gap_seconds = gap_seconds

    def set_reservoir_norm(self, norm: float) -> None:
        self.reservoir_norm = norm

    def finish(self) -> None:
        self.duration = time.perf_counter() - self.start_time

    @property
    def events_per_second(self) -> float:
        """Throughput over the run so far (events / elapsed seconds)."""
        elapsed = self.duration or (time.perf_counter() - self.start_time)
        return self.events / elapsed if elapsed > 0 else 0.0

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
            "lifetime_steps": self.lifetime_steps,
            "heartbeats": self.heartbeats,
            "checkpoints": self.checkpoints,
            "restarts": self.restarts,
            "unexpected_deaths": self.unexpected_deaths,
            "brain_death_gap_seconds": round(self.brain_death_gap_seconds, 6),
            "events": self.events,
            "events_per_second": round(self.events_per_second, 4),
            "reservoir_updates": self.reservoir_updates,
            "reservoir_norm": round(self.reservoir_norm, 6),
            "readout_updates": self.readout_updates,
            "average_prediction_error": round(self.average_prediction_error, 6),
            "recent_prediction_error": round(self.recent_prediction_error, 6),
            "habit_total_weight": round(self.habit_total_weight, 6),
            "habit_weight_change": round(self.habit_weight_change, 6),
            "habit_reinforcements": self.habit_reinforcements,
            "pruning_passes": self.pruning_passes,
            "pruned_pathways": self.pruned_pathways,
            "memory_trace_length": self.memory_trace_length,
            "trace_event_count": self.trace_event_count,
            "duration_seconds": round(self.duration, 6),
        }

    # ``to_dict`` is the canonical serialisation name; ``report`` is kept as an
    # alias used throughout Prompts 1-2.
    def to_dict(self) -> Dict[str, Any]:
        """Alias of :meth:`report` (canonical serialisation entry point)."""
        return self.report()

    def save_json(self, path: Union[str, Path]) -> None:
        """Write the metrics to ``path`` as pretty JSON."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)

    @classmethod
    def load_json(cls, path: Union[str, Path]) -> "Telemetry":
        """Reconstruct a Telemetry from a JSON file written by :meth:`save_json`.

        Rolling internals (error window) cannot be perfectly restored; cumulative
        counters are. This is sufficient for carrying lifetime metrics across a
        restart, which is the only use.
        """
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        telem = cls()
        for key in (
            "steps", "lifetime_steps", "heartbeats", "checkpoints", "restarts",
            "unexpected_deaths", "events", "reservoir_updates", "readout_updates",
            "pruning_passes", "pruned_pathways", "memory_trace_length",
            "trace_event_count", "habit_reinforcements",
        ):
            if key in data:
                setattr(telem, key, int(data[key]))
        for key in ("brain_death_gap_seconds", "reservoir_norm", "habit_total_weight"):
            if key in data:
                setattr(telem, key, float(data[key]))
        return telem

    def __str__(self) -> str:
        lines = ["Telemetry:"]
        for key, value in self.report().items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)
