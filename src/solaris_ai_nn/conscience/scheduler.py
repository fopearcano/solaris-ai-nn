"""Conscience scheduler -- run fast and slow modules at the right cadence.

The :class:`ConscienceScheduler` decides, per step, which spine phases run.
Cheap phases run every step; heavy scans (LOGOS, hypothesis,
auto-regeneration, consolidation, reports) run at slower cadences so the
runtime stays low-compute. Every scheduling decision is inspectable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ScheduleCadence:
    EVERY_STEP = "every_step"
    EVERY_N_STEPS = "every_n_steps"
    EVERY_SIMULATED_MINUTE = "every_simulated_minute"
    EVERY_SIMULATED_HOUR = "every_simulated_hour"
    EVERY_SIMULATED_DAY = "every_simulated_day"
    EVERY_SIMULATED_WEEK = "every_simulated_week"
    EVERY_SIMULATED_MONTH = "every_simulated_month"
    QUIET_WINDOW = "quiet_window"
    ANOMALY_WINDOW = "anomaly_window"
    EMERGENCY_ONLY = "emergency_only"

    ALL = (EVERY_STEP, EVERY_N_STEPS, EVERY_SIMULATED_MINUTE,
           EVERY_SIMULATED_HOUR, EVERY_SIMULATED_DAY, EVERY_SIMULATED_WEEK,
           EVERY_SIMULATED_MONTH, QUIET_WINDOW, ANOMALY_WINDOW,
           EMERGENCY_ONLY)


# Approximate step periods for simulated-time cadences (low-compute defaults).
_CADENCE_PERIOD = {
    ScheduleCadence.EVERY_SIMULATED_MINUTE: 1,
    ScheduleCadence.EVERY_SIMULATED_HOUR: 10,
    ScheduleCadence.EVERY_SIMULATED_DAY: 50,
    ScheduleCadence.EVERY_SIMULATED_WEEK: 200,
    ScheduleCadence.EVERY_SIMULATED_MONTH: 600,
}


@dataclass
class ScheduleSlot:
    """One phase's cadence and (for every_n_steps) period."""

    phase: str
    cadence: str = ScheduleCadence.EVERY_STEP
    every_n: int = 1
    runs: int = field(default=0, init=False)
    skips: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.cadence not in ScheduleCadence.ALL:
            raise ValueError(f"unknown cadence {self.cadence!r}")

    def due(self, step: int, emergency: bool = False,
            anomaly: bool = False, quiet: bool = False) -> bool:
        c = self.cadence
        if c == ScheduleCadence.EMERGENCY_ONLY:
            return emergency
        if emergency:
            # In an emergency only emergency/every-step slots run.
            return c == ScheduleCadence.EVERY_STEP
        if c == ScheduleCadence.EVERY_STEP:
            return True
        if c == ScheduleCadence.ANOMALY_WINDOW:
            return anomaly
        if c == ScheduleCadence.QUIET_WINDOW:
            return quiet
        if c == ScheduleCadence.EVERY_N_STEPS:
            return self.every_n <= 1 or step % self.every_n == 0
        period = _CADENCE_PERIOD.get(c, 1)
        return step % max(1, period) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {"phase": self.phase, "cadence": self.cadence,
                "every_n": self.every_n, "runs": self.runs,
                "skips": self.skips}


# Default cadence per spine phase: cheap phases every step, scans slower.
_DEFAULT_SLOTS = {
    "heartbeat": (ScheduleCadence.EVERY_STEP, 1),
    "read_only_sensory_poll": (ScheduleCadence.EVERY_STEP, 1),
    "stimulus_ingestion": (ScheduleCadence.EVERY_STEP, 1),
    "push_generation": (ScheduleCadence.EVERY_STEP, 1),
    "desire_synthesis": (ScheduleCadence.EVERY_STEP, 1),
    "action_candidate_generation": (ScheduleCadence.EVERY_STEP, 1),
    "executive_arbitration": (ScheduleCadence.EVERY_STEP, 1),
    "safety_governance_validation": (ScheduleCadence.EVERY_STEP, 1),
    "action_suggestion": (ScheduleCadence.EVERY_STEP, 1),
    "reaction_collection": (ScheduleCadence.EVERY_STEP, 1),
    "memory_update": (ScheduleCadence.EVERY_STEP, 1),
    "world_model_update": (ScheduleCadence.EVERY_N_STEPS, 5),
    "proto_language_update": (ScheduleCadence.EVERY_N_STEPS, 20),
    "hypothesis_update": (ScheduleCadence.EVERY_N_STEPS, 25),
    "logos_scan": (ScheduleCadence.EVERY_N_STEPS, 25),
    "autoregeneration_scan": (ScheduleCadence.EVERY_N_STEPS, 30),
    "inner_map_update": (ScheduleCadence.EVERY_N_STEPS, 10),
    "telemetry_checkpoint": (ScheduleCadence.EVERY_N_STEPS, 50),
    "latent_or_consolidation_window": (ScheduleCadence.EVERY_N_STEPS, 40),
}


@dataclass
class ConscienceScheduler:
    """Decides which phases run each step; deterministic and inspectable."""

    slots: Dict[str, ScheduleSlot] = field(default_factory=dict)
    skip_count: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if not self.slots:
            for phase, (cadence, n) in _DEFAULT_SLOTS.items():
                self.slots[phase] = ScheduleSlot(phase=phase, cadence=cadence,
                                                every_n=n)

    def set_slot(self, phase: str, cadence: str, every_n: int = 1) -> None:
        self.slots[phase] = ScheduleSlot(phase=phase, cadence=cadence,
                                        every_n=every_n)

    def due_phases(self, step: int, emergency: bool = False,
                   anomaly: bool = False, quiet: bool = False) -> Dict[str, bool]:
        """Phase -> whether it is due this step."""
        out: Dict[str, bool] = {}
        for phase, slot in self.slots.items():
            due = slot.due(step, emergency=emergency, anomaly=anomaly,
                           quiet=quiet)
            out[phase] = due
            if due:
                slot.runs += 1
            else:
                slot.skips += 1
                self.skip_count += 1
        return out

    def snapshot(self) -> Dict[str, Any]:
        return {
            "skip_count": self.skip_count,
            "slots": {p: s.to_dict() for p, s in self.slots.items()},
        }
