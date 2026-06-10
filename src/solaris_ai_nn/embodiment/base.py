"""Embodiment interfaces -- a simulated body in a simulated world. Nothing else.

This package gives Solaris-AI-NN a minimal sensorimotor loop: sensors produce
Solaris-compatible Stimulus/MeaningEvent signals, the neural bridge suggests
actions, effectors execute those actions **only inside the simulation**, the
environment produces consequences, and feedback returns as Reaction events.

Hard scope: there is no real-world actuation anywhere in this package. No
filesystem effectors (persistence/logging stays in `runtime/`), no network, no
OS, no subprocesses, no robotics. Action authority is *simulation-only*, and
the safety layer (`embodiment/safety.py`) enforces it. No consciousness is
claimed; "perceive" and "act" name data flows in a toy grid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..signals import canonical as C

Position = Tuple[int, int]


@dataclass
class SensorReading:
    """One sensed datum, convertible to a canonical Solaris signal."""

    sensor: str
    payload: str
    intensity: float = 0.0
    is_absence: bool = False
    novelty: float = 0.0
    modality: str = "simulated"
    kind: str = "Stimulus"  # "Stimulus" | "MeaningEvent"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_signal(self) -> C.Signal:
        """Convert to the canonical signal the bridge consumes."""
        origin = f"body:{self.sensor}"
        if self.kind == "MeaningEvent":
            return C.MeaningEvent(origin=origin, meaning=self.payload,
                                  novelty=self.novelty)
        return C.Stimulus(origin=origin, modality=self.modality,
                          payload=self.payload, intensity=self.intensity,
                          is_absence=self.is_absence)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sensor": self.sensor, "payload": self.payload,
            "intensity": self.intensity, "is_absence": self.is_absence,
            "novelty": self.novelty, "modality": self.modality,
            "kind": self.kind, "metadata": dict(self.metadata),
        }


@dataclass
class EffectorCommand:
    """A request to execute one simulated action (suggestion-sourced)."""

    action: str
    source: str = "suggestion"  # "suggestion" | "reflex" | "experiment"
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"action": self.action, "source": self.source,
                "params": dict(self.params)}


@dataclass
class ActionResult:
    """What happened when an effector ran a command in the simulation."""

    action: str
    executed: bool
    position_before: Optional[Position] = None
    position_after: Optional[Position] = None
    energy_cost: float = 0.0
    consequence: str = ""
    events: List[str] = field(default_factory=list)
    environment_changed: bool = False
    blocked_reason: Optional[str] = None

    @property
    def moved(self) -> bool:
        return (self.position_before is not None
                and self.position_after is not None
                and self.position_before != self.position_after)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action, "executed": self.executed,
            "position_before": list(self.position_before) if self.position_before else None,
            "position_after": list(self.position_after) if self.position_after else None,
            "energy_cost": self.energy_cost, "consequence": self.consequence,
            "events": list(self.events),
            "environment_changed": self.environment_changed,
            "blocked_reason": self.blocked_reason, "moved": self.moved,
        }


@dataclass
class EmbodimentState:
    """Aggregated body/world/energy state for persistence and the Inner MAP."""

    body: Dict[str, Any] = field(default_factory=dict)
    world: Dict[str, Any] = field(default_factory=dict)
    energy: Dict[str, Any] = field(default_factory=dict)
    last_action_result: Optional[Dict[str, Any]] = None
    sensor_history_summary: Dict[str, int] = field(default_factory=dict)
    action_history_summary: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "body": dict(self.body), "world": dict(self.world),
            "energy": dict(self.energy),
            "last_action_result": self.last_action_result,
            "sensor_history_summary": dict(self.sensor_history_summary),
            "action_history_summary": dict(self.action_history_summary),
        }


class Sensor:
    """Base sensor: reads body+environment, emits 0..n SensorReadings."""

    name: str = "sensor"

    def read(self, body: "Body", environment: "Environment") -> List[SensorReading]:
        raise NotImplementedError


class Effector:
    """Base effector: executes one family of simulated actions."""

    name: str = "effector"
    actions: Tuple[str, ...] = ()

    def handles(self, action: str) -> bool:
        return action in self.actions

    def execute(self, command: EffectorCommand, body: "Body",
                environment: "Environment") -> ActionResult:
        raise NotImplementedError


class Body:
    """Base body: owns sensors/effectors/energy; acts only in simulation."""

    def perceive(self) -> List[SensorReading]:
        raise NotImplementedError

    def act(self, command: EffectorCommand) -> ActionResult:
        raise NotImplementedError

    def snapshot(self) -> Dict[str, Any]:
        raise NotImplementedError


class Environment:
    """Base environment: deterministic, bounded, simulation-only."""

    def reset(self, seed: Optional[int] = None) -> None:
        raise NotImplementedError

    def step(self, action: str) -> Dict[str, Any]:
        raise NotImplementedError

    def sense(self, position: Optional[Position] = None) -> Dict[str, Any]:
        raise NotImplementedError

    def snapshot(self) -> Dict[str, Any]:
        raise NotImplementedError

    def to_ascii(self) -> str:
        raise NotImplementedError
