"""Pilot-4 actuator taxonomy -- classify what an actuator *would* be.

The :class:`ActuatorTaxonomy` classifies actuator categories and assigns each a
risk tier, for planning and risk classification only. In Pilot-4 every external
actuator category is **prohibited**; no adapter is implemented for any of them.
This is a map of the territory, not a set of doors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ActuatorCategory:
    INTERNAL_STATE_ACTION = "internal_state_action"
    SIMULATION_ACTION = "simulation_action"
    DRY_RUN_ACTION = "dry_run_action"
    READ_ONLY_OBSERVATION = "read_only_observation"
    FILE_WRITE_ACTION = "file_write_action"
    NETWORK_ACTION = "network_action"
    BROWSER_ACTION = "browser_action"
    OS_ACTION = "os_action"
    ROBOTIC_ACTION = "robotic_action"
    DEVICE_ACTION = "device_action"
    FINANCIAL_ACTION = "financial_action"
    COMMUNICATION_ACTION = "communication_action"
    PHYSICAL_WORLD_ACTION = "physical_world_action"
    UNKNOWN_ACTION = "unknown_action"

    ALL = (INTERNAL_STATE_ACTION, SIMULATION_ACTION, DRY_RUN_ACTION,
           READ_ONLY_OBSERVATION, FILE_WRITE_ACTION, NETWORK_ACTION,
           BROWSER_ACTION, OS_ACTION, ROBOTIC_ACTION, DEVICE_ACTION,
           FINANCIAL_ACTION, COMMUNICATION_ACTION, PHYSICAL_WORLD_ACTION,
           UNKNOWN_ACTION)
    # Categories that are safe / sandbox-scoped today.
    INTERNAL = frozenset({INTERNAL_STATE_ACTION, SIMULATION_ACTION,
                          DRY_RUN_ACTION, READ_ONLY_OBSERVATION})
    # Categories that touch the external world -- prohibited in Pilot-4.
    EXTERNAL = frozenset({FILE_WRITE_ACTION, NETWORK_ACTION, BROWSER_ACTION,
                          OS_ACTION, ROBOTIC_ACTION, DEVICE_ACTION,
                          FINANCIAL_ACTION, COMMUNICATION_ACTION,
                          PHYSICAL_WORLD_ACTION})


class ActuatorRiskTier:
    SAFE_INTERNAL = "safe_internal"
    SIMULATION_ONLY = "simulation_only"
    LOW_EXTERNAL_RISK = "low_external_risk"
    MEDIUM_EXTERNAL_RISK = "medium_external_risk"
    HIGH_EXTERNAL_RISK = "high_external_risk"
    PROHIBITED = "prohibited"
    UNKNOWN = "unknown"

    ALL = (SAFE_INTERNAL, SIMULATION_ONLY, LOW_EXTERNAL_RISK,
           MEDIUM_EXTERNAL_RISK, HIGH_EXTERNAL_RISK, PROHIBITED, UNKNOWN)


# Category -> (risk tier, prohibited-in-pilot4).
_CATEGORY_TIER = {
    ActuatorCategory.INTERNAL_STATE_ACTION: ActuatorRiskTier.SAFE_INTERNAL,
    ActuatorCategory.SIMULATION_ACTION: ActuatorRiskTier.SIMULATION_ONLY,
    ActuatorCategory.DRY_RUN_ACTION: ActuatorRiskTier.SIMULATION_ONLY,
    ActuatorCategory.READ_ONLY_OBSERVATION: ActuatorRiskTier.SAFE_INTERNAL,
    ActuatorCategory.FILE_WRITE_ACTION: ActuatorRiskTier.MEDIUM_EXTERNAL_RISK,
    ActuatorCategory.NETWORK_ACTION: ActuatorRiskTier.HIGH_EXTERNAL_RISK,
    ActuatorCategory.BROWSER_ACTION: ActuatorRiskTier.HIGH_EXTERNAL_RISK,
    ActuatorCategory.OS_ACTION: ActuatorRiskTier.HIGH_EXTERNAL_RISK,
    ActuatorCategory.ROBOTIC_ACTION: ActuatorRiskTier.HIGH_EXTERNAL_RISK,
    ActuatorCategory.DEVICE_ACTION: ActuatorRiskTier.HIGH_EXTERNAL_RISK,
    ActuatorCategory.FINANCIAL_ACTION: ActuatorRiskTier.HIGH_EXTERNAL_RISK,
    ActuatorCategory.COMMUNICATION_ACTION: ActuatorRiskTier.MEDIUM_EXTERNAL_RISK,
    ActuatorCategory.PHYSICAL_WORLD_ACTION: ActuatorRiskTier.HIGH_EXTERNAL_RISK,
    ActuatorCategory.UNKNOWN_ACTION: ActuatorRiskTier.UNKNOWN,
}


@dataclass
class ActuatorClass:
    """One actuator category with its planning-time risk classification."""

    category: str
    description: str
    risk_tier: str = ActuatorRiskTier.UNKNOWN
    prohibited_in_pilot4: bool = True
    examples: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.category not in ActuatorCategory.ALL:
            self.category = ActuatorCategory.UNKNOWN_ACTION
        # In Pilot-4, every external category is prohibited; internal/sim
        # categories are not "prohibited" but are still not enabled here.
        if self.category in ActuatorCategory.EXTERNAL:
            self.risk_tier = ActuatorRiskTier.PROHIBITED
            self.prohibited_in_pilot4 = True
        else:
            self.risk_tier = _CATEGORY_TIER.get(self.category,
                                                ActuatorRiskTier.UNKNOWN)
            self.prohibited_in_pilot4 = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ActuatorTaxonomy:
    """The full planning taxonomy of actuator categories."""

    classes: Dict[str, ActuatorClass] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.classes:
            self.classes = {c: ActuatorClass(category=c, description=c)
                            for c in ActuatorCategory.ALL}

    def classify(self, category: str) -> ActuatorClass:
        return self.classes.get(category,
                                ActuatorClass(ActuatorCategory.UNKNOWN_ACTION,
                                              "unknown"))

    def is_prohibited_in_pilot4(self, category: str) -> bool:
        return category in ActuatorCategory.EXTERNAL

    def prohibited_categories(self) -> List[str]:
        return sorted(ActuatorCategory.EXTERNAL)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "category_count": len(self.classes),
            "categories": list(ActuatorCategory.ALL),
            "risk_tiers": list(ActuatorRiskTier.ALL),
            "prohibited_categories": self.prohibited_categories(),
            "note": "taxonomy is for planning/risk classification only; no "
                    "external actuator adapter is implemented",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"classes": {c: k.to_dict() for c, k in self.classes.items()}}
