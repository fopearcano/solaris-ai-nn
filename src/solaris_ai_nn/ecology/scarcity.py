"""Scarcity -- need pressure without a teacher.

The model tracks how scarce signals and reward analogues are, how long
the system has gone without an expected signal, and a resource-like
"energy" that drains in lean phases and recovers in plenty. It exposes a
homeostasis-facing pressure dict (seek-signal, rest/consolidation,
uncertainty) so scarcity *creates* need rather than labelling it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ScarcityModel:
    """Deterministic scarcity accounting over the run."""

    signal_drought_steps: int = field(default=0, init=False)
    reward_drought_steps: int = field(default=0, init=False)
    missing_expected_signals: int = field(default=0, init=False)
    low_energy_steps: int = field(default=0, init=False)
    resource_level: float = field(default=1.0, init=False)  # [0, 1]
    steps_observed: int = field(default=0, init=False)

    def observe(self, had_signal: bool, had_reward: bool,
                expected_signal: bool, in_scarcity_phase: bool,
                ) -> None:
        """One step of scarcity bookkeeping."""
        self.steps_observed += 1
        self.signal_drought_steps = (0 if had_signal
                                     else self.signal_drought_steps + 1)
        self.reward_drought_steps = (0 if had_reward
                                     else self.reward_drought_steps + 1)
        if expected_signal and not had_signal:
            self.missing_expected_signals += 1
        # Resource drains during reward drought / scarcity, recovers on
        # reward; never leaves [0, 1].
        drain = 0.04 if (in_scarcity_phase or not had_reward) else 0.0
        gain = 0.08 if had_reward else 0.0
        self.resource_level = max(0.0, min(
            1.0, self.resource_level - drain + gain))
        if self.resource_level < 0.3:
            self.low_energy_steps += 1

    def pressures(self) -> Dict[str, float]:
        """Homeostasis-facing pressure (never commands)."""
        seek = min(1.0, self.signal_drought_steps / 10.0)
        reward_pressure = min(1.0, self.reward_drought_steps / 20.0)
        rest = max(0.0, 1.0 - self.resource_level)
        uncertainty = min(1.0, self.missing_expected_signals
                          / max(1, self.steps_observed) * 5.0)
        return {
            "seek_signal_pressure": round(seek, 4),
            "reward_scarcity_pressure": round(reward_pressure, 4),
            "rest_consolidation_pressure": round(rest, 4),
            "scarcity_uncertainty_pressure": round(uncertainty, 4),
            "resource_level": round(self.resource_level, 4),
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "signal_drought_steps": self.signal_drought_steps,
            "reward_drought_steps": self.reward_drought_steps,
            "missing_expected_signals": self.missing_expected_signals,
            "low_energy_steps": self.low_energy_steps,
            "resource_level": round(self.resource_level, 4),
            "pressures": self.pressures(),
        }
