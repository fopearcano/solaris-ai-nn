"""Pilot-4 emergency requirements -- internal stop now; physical specs later.

The :class:`EmergencyRequirementSet` documents the emergency-stop requirements
that any future external actuation would need. The existing emergency stop
remains internal/software; the future physical requirements (kill switch, power
cut, deadman timer) are documentation/spec only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class EmergencyRequirement:
    """One emergency requirement; ``physical`` ones are future/spec-only."""

    name: str
    description: str
    physical: bool = False
    spec_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


_REQUIREMENTS = (
    ("software_emergency_stop", "a software emergency stop", False),
    ("physical_kill_switch", "a physical kill switch for hardware", True),
    ("power_cut_option", "a power-cut option for hardware", True),
    ("action_rate_limiter", "an action rate limiter", False),
    ("supervisor_heartbeat", "a supervisor heartbeat", False),
    ("deadman_timer", "a deadman timer", True),
    ("safe_default_stop", "a safe default stop on uncertainty", False),
    ("log_final_action", "log the final action before stopping", False),
    ("disable_external_authority_on_restart",
     "disable external authority on restart", False),
    ("manual_reset_required", "require a manual reset after emergency", True),
)


@dataclass
class EmergencyRequirementSet:
    """Holds emergency requirements; physical ones are spec-only."""

    requirements: List[EmergencyRequirement] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.requirements:
            self.requirements = [
                EmergencyRequirement(name=n, description=d, physical=phys,
                                     spec_only=phys)
                for n, d, phys in _REQUIREMENTS]

    def names(self) -> List[str]:
        return [r.name for r in self.requirements]

    def has_requirement(self, name: str) -> bool:
        return any(r.name == name for r in self.requirements)

    def physical_requirements(self) -> List[str]:
        return [r.name for r in self.requirements if r.physical]

    @property
    def completeness(self) -> float:
        return 1.0 if self.requirements else 0.0

    def snapshot(self) -> Dict[str, Any]:
        return {
            "requirement_count": len(self.requirements),
            "names": self.names(),
            "physical_requirements": self.physical_requirements(),
            "note": "the current emergency stop is internal/software; physical "
                    "requirements are documentation/spec only",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"requirements": [r.to_dict() for r in self.requirements]}
