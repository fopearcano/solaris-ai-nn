"""Embodiment profiles -- named, bounded, simulation-only sandbox bodies.

Each :class:`EmbodimentProfile` pins which simulated actuators and action
types are available. Every profile is simulation-only or dry-run; there is no
device/robot/browser/OS profile, and ``real_world_authority`` is always False.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .actions import MotorActionType


class EmbodimentProfileName:
    NO_BODY = "no_body"
    GRIDWORLD_MINIMAL = "gridworld_minimal"
    GRIDWORLD_BOUNDARY = "gridworld_boundary"
    GRIDWORLD_REWARD_DANGER = "gridworld_reward_danger"
    GRIDWORLD_OBJECT = "gridworld_object"
    DRY_RUN_MOTOR = "dry_run_motor"
    PILOT3_LIMITED_EMBODIMENT_PLAN = "pilot3_limited_embodiment_plan"

    ALL = (NO_BODY, GRIDWORLD_MINIMAL, GRIDWORLD_BOUNDARY,
           GRIDWORLD_REWARD_DANGER, GRIDWORLD_OBJECT, DRY_RUN_MOTOR,
           PILOT3_LIMITED_EMBODIMENT_PLAN)


@dataclass
class EmbodimentProfile:
    """A bounded, simulation-only embodiment configuration."""

    profile_id: str
    description: str
    enable_gridworld: bool = True
    enable_internal_actions: bool = True
    dry_run: bool = False
    plan_only: bool = False
    allowed_action_types: List[str] = field(default_factory=list)
    real_world_authority: bool = False

    def __post_init__(self) -> None:
        # Invariant: profiles never carry real-world authority.
        self.real_world_authority = False

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "simulation_or_dry_run_only": True}


def _build() -> Dict[str, EmbodimentProfile]:
    A = MotorActionType
    internal = [A.NO_ACTION, A.REST, A.WAIT, A.REQUEST_CONSOLIDATION,
                A.REQUEST_REPLAY]
    move = [A.LOOK, A.MOVE_NORTH, A.MOVE_SOUTH, A.MOVE_EAST, A.MOVE_WEST,
            A.WAIT, A.REST]
    profiles = {
        EmbodimentProfileName.NO_BODY: EmbodimentProfile(
            EmbodimentProfileName.NO_BODY,
            "internal only: no_action/rest/replay/consolidation",
            enable_gridworld=False, allowed_action_types=list(internal)),
        EmbodimentProfileName.GRIDWORLD_MINIMAL: EmbodimentProfile(
            EmbodimentProfileName.GRIDWORLD_MINIMAL,
            "move/look/wait in a tiny grid",
            allowed_action_types=list(move)),
        EmbodimentProfileName.GRIDWORLD_BOUNDARY: EmbodimentProfile(
            EmbodimentProfileName.GRIDWORLD_BOUNDARY,
            "boundary inspection in a grid",
            allowed_action_types=move + [A.INSPECT_BOUNDARY,
                                         A.EMIT_SIMULATED_PING]),
        EmbodimentProfileName.GRIDWORLD_REWARD_DANGER: EmbodimentProfile(
            EmbodimentProfileName.GRIDWORLD_REWARD_DANGER,
            "reward/danger analogues in a grid",
            allowed_action_types=move + [A.APPROACH_SIGNAL, A.AVOID_SIGNAL,
                                         A.TOUCH_SIMULATED_OBJECT]),
        EmbodimentProfileName.GRIDWORLD_OBJECT: EmbodimentProfile(
            EmbodimentProfileName.GRIDWORLD_OBJECT,
            "simulated pick/drop object in a grid",
            allowed_action_types=move + [A.PICK_SIMULATED_OBJECT,
                                         A.DROP_SIMULATED_OBJECT,
                                         A.MARK_SIMULATED_LOCATION]),
        EmbodimentProfileName.DRY_RUN_MOTOR: EmbodimentProfile(
            EmbodimentProfileName.DRY_RUN_MOTOR,
            "records proposed actions only; no simulation state change",
            dry_run=True, allowed_action_types=list(MotorActionType.ALL)),
        EmbodimentProfileName.PILOT3_LIMITED_EMBODIMENT_PLAN: EmbodimentProfile(
            EmbodimentProfileName.PILOT3_LIMITED_EMBODIMENT_PLAN,
            "planning profile only; starts no run",
            enable_gridworld=False, plan_only=True,
            allowed_action_types=list(internal)),
    }
    return profiles


@dataclass
class EmbodimentProfileRegistry:
    """Holds the built-in embodiment profiles."""

    profiles: Dict[str, EmbodimentProfile] = field(default_factory=_build)

    def get(self, profile_id: str):
        return self.profiles.get(profile_id)

    def require(self, profile_id: str) -> EmbodimentProfile:
        profile = self.profiles.get(profile_id)
        if profile is None:
            raise KeyError(f"unknown embodiment profile {profile_id!r}")
        return profile

    def ids(self) -> List[str]:
        return sorted(self.profiles)

    def has_real_world_profile(self) -> bool:
        return any(p.real_world_authority for p in self.profiles.values())

    def snapshot(self) -> Dict[str, Any]:
        return {"profile_count": len(self.profiles), "profiles": self.ids(),
                "has_real_world_profile": self.has_real_world_profile()}
