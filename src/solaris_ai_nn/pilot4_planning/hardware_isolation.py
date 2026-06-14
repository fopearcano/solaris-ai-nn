"""Pilot-4 hardware isolation requirements -- documented, never exercised.

The :class:`HardwareIsolationPlan` documents the isolation requirements that
*would* apply if hardware were ever connected. No hardware is connected, no
device is scanned, and nothing is accessed. This is planning only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class HardwareIsolationRequirement:
    """One future hardware-isolation requirement (documentation only)."""

    name: str
    description: str
    mandatory: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


_REQUIREMENTS = (
    ("separate_sandbox_machine", "run on a separate, isolated sandbox machine"),
    ("no_direct_network_by_default", "no direct network access by default"),
    ("physical_kill_switch", "a physical kill switch on any actuator"),
    ("power_isolation", "independent power isolation / cut option"),
    ("actuator_simulator_first", "an actuator simulator validated first"),
    ("test_harness", "a test harness before any real connection"),
    ("manual_enable_switch", "a manual, physical enable switch"),
    ("hardware_whitelist", "a hardware whitelist (deny by default)"),
    ("one_action_at_a_time", "one-action-at-a-time mode"),
    ("rate_limiter", "a hardware-level rate limiter"),
    ("external_supervisor", "an independent external supervisor"),
    ("independent_logger", "an independent, tamper-evident logger"),
)


@dataclass
class HardwareIsolationPlan:
    """Holds future hardware-isolation requirements; performs no access."""

    requirements: List[HardwareIsolationRequirement] = field(
        default_factory=list)
    hardware_connected: bool = False
    hardware_scanned: bool = False

    def __post_init__(self) -> None:
        if not self.requirements:
            self.requirements = [HardwareIsolationRequirement(n, d)
                                 for n, d in _REQUIREMENTS]
        # Invariants: no hardware is connected or scanned.
        self.hardware_connected = False
        self.hardware_scanned = False

    def names(self) -> List[str]:
        return [r.name for r in self.requirements]

    def has_requirement(self, name: str) -> bool:
        return any(r.name == name for r in self.requirements)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "requirement_count": len(self.requirements),
            "names": self.names(),
            "hardware_connected": False,
            "hardware_scanned": False,
            "note": "planning only; no hardware is connected, scanned, or "
                    "accessed",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"requirements": [r.to_dict() for r in self.requirements],
                "hardware_connected": False, "hardware_scanned": False}
