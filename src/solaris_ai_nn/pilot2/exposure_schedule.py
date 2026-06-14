"""Pilot-2 exposure schedule -- alternate baseline and exposure windows.

The :class:`ExposureSchedule` lays out bounded windows under different
exposure conditions (nursery-only, sensory-only, mixed, quiet, focus windows,
low/high variability, recovery). It alternates baseline and exposure windows,
preserves quiet periods for latent replay, avoids uncontrolled floods, keeps
comparison windows explicit, and labels any simulated acceleration as such.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ExposureCondition:
    NURSERY_ONLY = "nursery_only"
    SENSORY_ONLY = "sensory_only"
    MIXED = "mixed"
    QUIET_READ_ONLY = "quiet_read_only"
    NUMERIC_STREAM_FOCUS = "numeric_stream_focus"
    TEXT_STREAM_FOCUS = "text_stream_focus"
    FOLDER_CHANGE_FOCUS = "folder_change_focus"
    LOW_RATE_ENVIRONMENT = "low_rate_environment"
    HIGH_VARIABILITY_ENVIRONMENT = "high_variability_environment"
    RECOVERY_WINDOW = "recovery_window"

    ALL = (NURSERY_ONLY, SENSORY_ONLY, MIXED, QUIET_READ_ONLY,
           NUMERIC_STREAM_FOCUS, TEXT_STREAM_FOCUS, FOLDER_CHANGE_FOCUS,
           LOW_RATE_ENVIRONMENT, HIGH_VARIABILITY_ENVIRONMENT, RECOVERY_WINDOW)
    QUIET = frozenset({QUIET_READ_ONLY, RECOVERY_WINDOW})


@dataclass
class ExposureWindow:
    """One scheduled window with a condition and bounded length."""

    index: int
    condition: str
    steps: int = 20
    simulated_acceleration: bool = False
    note: str = ""

    def __post_init__(self) -> None:
        if self.condition not in ExposureCondition.ALL:
            self.condition = ExposureCondition.MIXED
        self.is_quiet = self.condition in ExposureCondition.QUIET

    def to_dict(self) -> Dict[str, Any]:
        return {"index": self.index, "condition": self.condition,
                "steps": self.steps, "is_quiet": self.is_quiet,
                "simulated_acceleration": self.simulated_acceleration,
                "note": self.note}


@dataclass
class ExposureSchedule:
    """An ordered list of bounded exposure windows."""

    windows: List[ExposureWindow] = field(default_factory=list)

    @classmethod
    def alternating(cls, cycles: int = 2, window_steps: int = 20,
                    simulated: bool = False) -> "ExposureSchedule":
        """Build a baseline/exposure alternation with quiet windows between."""
        sched = cls()
        idx = 0
        for _ in range(max(1, cycles)):
            for cond in (ExposureCondition.NURSERY_ONLY,
                         ExposureCondition.QUIET_READ_ONLY,
                         ExposureCondition.SENSORY_ONLY,
                         ExposureCondition.MIXED,
                         ExposureCondition.RECOVERY_WINDOW):
                sched.windows.append(ExposureWindow(
                    index=idx, condition=cond, steps=window_steps,
                    simulated_acceleration=simulated,
                    note=("baseline" if cond == ExposureCondition.NURSERY_ONLY
                          else "exposure" if cond in (
                              ExposureCondition.SENSORY_ONLY,
                              ExposureCondition.MIXED) else "quiet")))
                idx += 1
        return sched

    @property
    def quiet_window_count(self) -> int:
        return sum(1 for w in self.windows if w.is_quiet)

    @property
    def total_steps(self) -> int:
        return sum(w.steps for w in self.windows)

    def comparison_windows(self) -> Dict[str, List[int]]:
        """Group window indices by condition for explicit comparison."""
        groups: Dict[str, List[int]] = {}
        for w in self.windows:
            groups.setdefault(w.condition, []).append(w.index)
        return groups

    def validate(self) -> List[str]:
        """Return warnings about the schedule (never raises)."""
        warnings: List[str] = []
        if self.quiet_window_count == 0:
            warnings.append("no quiet windows: latent replay may be starved")
        if self.total_steps > 100000:
            warnings.append("schedule is very long; risk of event flood")
        for w in self.windows:
            if w.steps > 5000 and not w.simulated_acceleration:
                warnings.append(
                    f"window {w.index} is long without simulated label")
        return warnings

    def to_dict(self) -> Dict[str, Any]:
        return {
            "window_count": len(self.windows),
            "quiet_window_count": self.quiet_window_count,
            "total_steps": self.total_steps,
            "comparison_windows": self.comparison_windows(),
            "warnings": self.validate(),
            "windows": [w.to_dict() for w in self.windows],
        }
