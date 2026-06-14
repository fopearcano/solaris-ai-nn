"""Affordance model -- what (simulated) actions a situation seems to allow.

The :class:`AffordanceDetector` reads GridWorld / ecology / world-model /
active-perception state and produces scoped :class:`Affordance`s. Read-only
sensory sources are *observable only* and never manipulable; real-world files
and folders are never action targets; and a real-world affordance is
representable only as ``forbidden_real_world``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .actions import MotorActionScope


class AffordanceType:
    OBSERVABLE = "observable"
    APPROACHABLE = "approachable"
    AVOIDABLE = "avoidable"
    INSPECTABLE = "inspectable"
    REACHABLE_IN_SIMULATION = "reachable_in_simulation"
    BOUNDARY = "boundary"
    DANGER_ANALOGUE = "danger_analogue"
    REWARD_ANALOGUE = "reward_analogue"
    UNKNOWN_REGION = "unknown_region"
    REST_ZONE = "rest_zone"
    FORBIDDEN_REAL_WORLD = "forbidden_real_world"

    ALL = (OBSERVABLE, APPROACHABLE, AVOIDABLE, INSPECTABLE,
           REACHABLE_IN_SIMULATION, BOUNDARY, DANGER_ANALOGUE,
           REWARD_ANALOGUE, UNKNOWN_REGION, REST_ZONE, FORBIDDEN_REAL_WORLD)


@dataclass
class Affordance:
    """One scoped affordance with the target it refers to."""

    affordance_type: str
    target_ref: str
    scope: str = MotorActionScope.SIMULATION_ONLY
    manipulable: bool = False
    detail: str = ""

    def __post_init__(self) -> None:
        if self.affordance_type not in AffordanceType.ALL:
            self.affordance_type = AffordanceType.UNKNOWN_REGION
        # A read-only / forbidden affordance is never manipulable.
        if self.affordance_type in (AffordanceType.OBSERVABLE,
                                    AffordanceType.FORBIDDEN_REAL_WORLD):
            self.manipulable = False
        if self.affordance_type == AffordanceType.FORBIDDEN_REAL_WORLD:
            self.scope = MotorActionScope.FORBIDDEN_REAL_WORLD

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AffordanceMap:
    """A collection of affordances for the current situation."""

    affordances: List[Affordance] = field(default_factory=list)

    def add(self, affordance: Affordance) -> None:
        self.affordances.append(affordance)

    def by_type(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for a in self.affordances:
            out[a.affordance_type] = out.get(a.affordance_type, 0) + 1
        return out

    def manipulable_targets(self) -> List[str]:
        return [a.target_ref for a in self.affordances if a.manipulable]

    def to_dict(self) -> Dict[str, Any]:
        return {"affordance_count": len(self.affordances),
                "by_type": self.by_type(),
                "affordances": [a.to_dict() for a in self.affordances]}


@dataclass
class AffordanceDetector:
    """Builds a scoped affordance map from situation state (read-only)."""

    def detect(self, *, grid_world: Any = None,
               sensory_sources: Optional[List[Dict[str, Any]]] = None,
               world_model_nodes: Optional[List[str]] = None,
               ) -> AffordanceMap:
        amap = AffordanceMap()
        # GridWorld affordances (simulation-only, manipulable in simulation).
        if grid_world is not None:
            amap.add(Affordance(AffordanceType.REACHABLE_IN_SIMULATION,
                                "gridworld:agent",
                                scope=MotorActionScope.SANDBOX_ONLY,
                                manipulable=True))
            amap.add(Affordance(AffordanceType.BOUNDARY, "gridworld:wall",
                                scope=MotorActionScope.SANDBOX_ONLY))
            amap.add(Affordance(AffordanceType.REST_ZONE, "gridworld:rest",
                                scope=MotorActionScope.INTERNAL_ONLY))
            objects = getattr(grid_world, "objects", {}) or {}
            kinds = {k for k in objects.values()}
            if "reward" in kinds:
                amap.add(Affordance(AffordanceType.REWARD_ANALOGUE,
                                    "gridworld:reward",
                                    scope=MotorActionScope.SANDBOX_ONLY,
                                    manipulable=True))
            if "danger" in kinds:
                amap.add(Affordance(AffordanceType.DANGER_ANALOGUE,
                                    "gridworld:danger",
                                    scope=MotorActionScope.SANDBOX_ONLY))
            if "unknown" in kinds:
                amap.add(Affordance(AffordanceType.UNKNOWN_REGION,
                                    "gridworld:unknown",
                                    scope=MotorActionScope.SANDBOX_ONLY,
                                    manipulable=True))
        # Read-only sensory sources: observable only, never manipulable.
        for src in (sensory_sources or []):
            amap.add(Affordance(
                AffordanceType.OBSERVABLE,
                f"sensory:{src.get('source_id', '?')}",
                scope=MotorActionScope.READ_ONLY_OBSERVATION,
                manipulable=False,
                detail="read-only sensory source; never an action target"))
        # World-model nodes are inspectable in simulation.
        for node in (world_model_nodes or [])[:16]:
            amap.add(Affordance(AffordanceType.INSPECTABLE, f"wm:{node}",
                                scope=MotorActionScope.SIMULATION_ONLY))
        return amap

    def forbidden_target(self, target: str) -> Affordance:
        """Any real-world file/folder/device target is forbidden."""
        return Affordance(AffordanceType.FORBIDDEN_REAL_WORLD, target,
                          scope=MotorActionScope.FORBIDDEN_REAL_WORLD,
                          detail="real-world target; never actionable")
