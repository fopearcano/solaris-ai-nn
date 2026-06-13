"""Cycles -- the rhythms a developmental world runs on.

Day/night, active/quiet, scarcity, recovery, and seasonal cycles each
move through phases on fixed periods. The :class:`CycleManager` reports
the current phase, modulates how often (and how strongly) stimuli arrive,
and logs every phase change so reports can show what rhythm the system
actually lived through. Deterministic with the nursery seed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


class CycleType:
    DAY_NIGHT = "day_night"
    ACTIVE_QUIET = "active_quiet"
    SIGNAL_SILENCE = "signal_silence"
    REWARD_SCARCITY = "reward_scarcity"
    DANGER_RECOVERY = "danger_recovery"
    NOVELTY_DECAY = "novelty_decay"
    CONSOLIDATION_WINDOW = "consolidation_window"
    SEASONAL_CYCLE = "seasonal_cycle"

    ALL = (DAY_NIGHT, ACTIVE_QUIET, SIGNAL_SILENCE, REWARD_SCARCITY,
           DANGER_RECOVERY, NOVELTY_DECAY, CONSOLIDATION_WINDOW,
           SEASONAL_CYCLE)


# cycle type -> (period in steps, ordered phase names).
_CYCLE_SPECS: Dict[str, Tuple[int, Tuple[str, ...]]] = {
    CycleType.DAY_NIGHT: (24, ("day", "night")),
    CycleType.ACTIVE_QUIET: (16, ("active", "quiet")),
    CycleType.SIGNAL_SILENCE: (20, ("signal", "silence")),
    CycleType.REWARD_SCARCITY: (40, ("plenty", "scarcity")),
    CycleType.DANGER_RECOVERY: (30, ("danger", "recovery")),
    CycleType.NOVELTY_DECAY: (50, ("novel", "familiar")),
    CycleType.CONSOLIDATION_WINDOW: (60, ("wake", "consolidation")),
    CycleType.SEASONAL_CYCLE: (200, ("spring", "summer", "autumn",
                                     "winter")),
}

# (cycle type, phase) -> (frequency multiplier, intensity multiplier).
_PHASE_MODULATION: Dict[Tuple[str, str], Tuple[float, float]] = {
    (CycleType.DAY_NIGHT, "day"): (1.3, 1.0),
    (CycleType.DAY_NIGHT, "night"): (0.4, 0.7),
    (CycleType.ACTIVE_QUIET, "active"): (1.3, 1.0),
    (CycleType.ACTIVE_QUIET, "quiet"): (0.5, 0.8),
    (CycleType.SIGNAL_SILENCE, "signal"): (1.2, 1.0),
    (CycleType.SIGNAL_SILENCE, "silence"): (0.2, 0.5),
    (CycleType.REWARD_SCARCITY, "plenty"): (1.1, 1.0),
    (CycleType.REWARD_SCARCITY, "scarcity"): (0.7, 0.9),
    (CycleType.DANGER_RECOVERY, "danger"): (1.0, 1.1),
    (CycleType.DANGER_RECOVERY, "recovery"): (0.6, 0.8),
    (CycleType.CONSOLIDATION_WINDOW, "wake"): (1.1, 1.0),
    (CycleType.CONSOLIDATION_WINDOW, "consolidation"): (0.3, 0.6),
}


@dataclass
class Cycle:
    """One periodic rhythm."""

    cycle_type: str
    period: int
    phases: Tuple[str, ...]
    phase_offset: int = 0

    def phase_at(self, step: int) -> str:
        if self.period <= 0 or not self.phases:
            return ""
        position = (step + self.phase_offset) % self.period
        bucket = self.period // len(self.phases) or 1
        index = min(position // bucket, len(self.phases) - 1)
        return self.phases[index]

    def to_dict(self) -> Dict[str, Any]:
        return {"cycle_type": self.cycle_type, "period": self.period,
                "phases": list(self.phases)}


@dataclass
class CycleState:
    """The current phase of every active cycle."""

    phases: Dict[str, str] = field(default_factory=dict)
    step: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class CycleManager:
    """Computes phases, modulation, and phase-change history."""

    active_cycles: List[str] = field(
        default_factory=lambda: [CycleType.DAY_NIGHT,
                                 CycleType.SIGNAL_SILENCE])
    phase_offsets: Dict[str, int] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    _last_phases: Dict[str, str] = field(default_factory=dict, init=False)
    phase_changes: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.cycles: Dict[str, Cycle] = {}
        for cycle_type in self.active_cycles:
            period, phases = _CYCLE_SPECS[cycle_type]
            self.cycles[cycle_type] = Cycle(
                cycle_type=cycle_type, period=period, phases=phases,
                phase_offset=self.phase_offsets.get(cycle_type, 0))

    def state_at(self, step: int) -> CycleState:
        phases = {ct: cycle.phase_at(step)
                  for ct, cycle in self.cycles.items()}
        return CycleState(phases=phases, step=step)

    def update(self, step: int) -> CycleState:
        """Advance, recording any phase change."""
        state = self.state_at(step)
        for cycle_type, phase in state.phases.items():
            previous = self._last_phases.get(cycle_type)
            if previous is not None and previous != phase:
                self.phase_changes += 1
                self.history.append({
                    "step": step, "cycle": cycle_type,
                    "from": previous, "to": phase,
                    "timestamp": time.time()})
                self.history = self.history[-200:]
            self._last_phases[cycle_type] = phase
        return state

    def modulation(self, state: CycleState) -> Tuple[float, float]:
        """(frequency multiplier, intensity multiplier) for a phase set."""
        frequency = 1.0
        intensity = 1.0
        for cycle_type, phase in state.phases.items():
            freq_mult, int_mult = _PHASE_MODULATION.get(
                (cycle_type, phase), (1.0, 1.0))
            frequency *= freq_mult
            intensity *= int_mult
        return (round(frequency, 4), round(intensity, 4))

    def in_silence_phase(self, state: CycleState) -> bool:
        return any(phase in ("silence", "night", "quiet",
                             "consolidation")
                   for phase in state.phases.values())

    def snapshot(self) -> Dict[str, Any]:
        return {
            "active_cycles": list(self.active_cycles),
            "cycles": {ct: c.to_dict()
                       for ct, c in self.cycles.items()},
            "phase_changes": self.phase_changes,
            "recent_changes": self.history[-5:],
        }
