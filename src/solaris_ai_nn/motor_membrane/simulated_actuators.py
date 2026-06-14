"""Simulated actuators -- effect only simulation/internal state, never reality.

:class:`GridWorldActuator` drives the existing GridWorld sandbox body;
:class:`InternalActuator` issues internal requests (consolidation, replay,
report, checkpoint). Neither touches a real device, and neither writes to the
filesystem except the approved state/artifact logs (via the ledger). Every
result is a :class:`ActuatorResult` with ``simulated = True``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .actions import MotorAction, MotorActionType


@dataclass
class ActuatorResult:
    """The (simulated/internal) outcome of one actuator execution."""

    action_id: str
    action_type: str
    simulated: bool = True
    real_world_authority: bool = False
    effect_summary: str = ""
    reaction_valence: float = 0.0
    information_gain: float = 0.0
    state_changed: bool = False
    detail: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


class SimulatedActuator:
    """Base class: actuators only affect simulation/internal state."""

    name = "simulated_actuator"

    def can_handle(self, action: MotorAction) -> bool:  # pragma: no cover
        raise NotImplementedError

    def execute(self, action: MotorAction) -> ActuatorResult:  # pragma: no cover
        raise NotImplementedError


# GridWorld action-type -> GridWorld.step() action name.
_GRID_MAP = {
    MotorActionType.LOOK: "look",
    MotorActionType.REST: "rest",
    MotorActionType.WAIT: "rest",
    MotorActionType.MOVE_NORTH: "move_north",
    MotorActionType.MOVE_SOUTH: "move_south",
    MotorActionType.MOVE_EAST: "move_east",
    MotorActionType.MOVE_WEST: "move_west",
    MotorActionType.APPROACH_SIGNAL: "approach_signal",
    MotorActionType.AVOID_SIGNAL: "avoid_signal",
    MotorActionType.EMIT_SIMULATED_PING: "emit_ping",
    MotorActionType.TOUCH_SIMULATED_OBJECT: "touch_object",
    MotorActionType.INSPECT_BOUNDARY: "look",
}


class GridWorldActuator(SimulatedActuator):
    """Drives a GridWorld sandbox body (simulation-only)."""

    name = "gridworld_actuator"

    def __init__(self, world: Any) -> None:
        self.world = world
        self._marks: Dict[str, Any] = {}
        self._carried: Optional[str] = None

    def can_handle(self, action: MotorAction) -> bool:
        return action.action_type in MotorActionType.GRIDWORLD

    def execute(self, action: MotorAction) -> ActuatorResult:
        at = action.action_type
        if at == MotorActionType.MARK_SIMULATED_LOCATION:
            pos = tuple(getattr(self.world, "agent_pos", (0, 0)))
            self._marks[str(pos)] = action.action_id
            return ActuatorResult(action.action_id, at, effect_summary=
                                  f"marked {pos}", state_changed=True,
                                  detail={"marked": list(pos)})
        if at == MotorActionType.PICK_SIMULATED_OBJECT:
            step = self.world.step("touch_object")
            picked = any("touched:" in e for e in step.get("events", []))
            if picked:
                self._carried = "object"
            return self._from_step(action, step,
                                   extra={"carried": self._carried})
        if at == MotorActionType.DROP_SIMULATED_OBJECT:
            dropped, self._carried = self._carried, None
            return ActuatorResult(action.action_id, at,
                                  effect_summary=f"dropped {dropped}",
                                  state_changed=bool(dropped),
                                  detail={"dropped": dropped})
        grid_action = _GRID_MAP.get(at, "rest")
        step = self.world.step(grid_action)
        return self._from_step(action, step)

    def _from_step(self, action: MotorAction, step: Dict[str, Any],
                   extra: Optional[Dict[str, Any]] = None) -> ActuatorResult:
        blocked = step.get("blocked")
        events = step.get("events", [])
        changed = bool(step.get("environment_changed")) \
            or step.get("position_before") != step.get("position_after")
        # Simulated reaction valence: reward-ish events positive, blocks small
        # negative -- an *internal* signal, never a real-world outcome.
        valence = 0.0
        joined = ",".join(events)
        if "reward" in joined or "touched:reward" in joined:
            valence = 0.8
        elif "danger" in joined:
            valence = -0.6
        elif blocked:
            valence = -0.2
        elif changed:
            valence = 0.2
        info_gain = 0.3 if events and not blocked else 0.05
        detail = {"step": step}
        if extra:
            detail.update(extra)
        return ActuatorResult(
            action.action_id, action.action_type,
            effect_summary=(f"blocked:{blocked}" if blocked
                            else ",".join(events) or "no_event"),
            reaction_valence=valence, information_gain=info_gain,
            state_changed=changed, detail=detail)


class InternalActuator(SimulatedActuator):
    """Issues internal requests only (consolidation/replay/report/checkpoint)."""

    name = "internal_actuator"

    _SUPPORTED = {
        MotorActionType.REQUEST_CONSOLIDATION: "consolidation",
        MotorActionType.REQUEST_REPLAY: "latent_replay",
        MotorActionType.NO_ACTION: "no_action",
        MotorActionType.WAIT: "wait",
        MotorActionType.REST: "rest",
    }

    def can_handle(self, action: MotorAction) -> bool:
        return action.action_type in self._SUPPORTED

    def execute(self, action: MotorAction) -> ActuatorResult:
        request = self._SUPPORTED.get(action.action_type, "no_action")
        return ActuatorResult(
            action.action_id, action.action_type,
            effect_summary=f"internal_request:{request}",
            reaction_valence=0.0, information_gain=0.0,
            state_changed=False, detail={"request": request})
