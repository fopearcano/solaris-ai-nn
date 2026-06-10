"""SimulatedBody -- sensors, effectors, energy, and a position in a grid.

The body perceives the environment through its sensors (emitting canonical
Stimulus events), receives action *suggestions* from the neural bridge, and
executes them **only** if the embodiment safety layer approves and an effector
exists for them -- always and exclusively inside the simulated environment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .action_space import ALLOWED_ACTIONS, FORBIDDEN_ACTIONS
from .base import (
    ActionResult,
    Body,
    EffectorCommand,
    Environment,
    Position,
    Sensor,
    SensorReading,
)
from .effectors import default_effectors
from .energy import EnergyModel
from .safety import EmbodimentSafety
from .sensors import default_sensors


@dataclass
class SimulatedBody(Body):
    """A body that exists only inside its simulated environment."""

    environment: Environment
    energy: EnergyModel = field(default_factory=EnergyModel)
    sensors: List[Sensor] = field(default_factory=default_sensors)
    effectors: List[Any] = field(default_factory=default_effectors)
    safety: EmbodimentSafety = field(default_factory=EmbodimentSafety)
    name: str = "simulated_body"

    last_readings: List[SensorReading] = field(default_factory=list, init=False)
    last_result: Optional[ActionResult] = field(default=None, init=False)
    actions_executed: int = 0
    actions_blocked: int = 0

    @property
    def position(self) -> Position:
        """The body's position (the environment is the source of truth)."""
        return self.environment.agent_pos

    # -- perception ----------------------------------------------------------

    def perceive(self) -> List[SensorReading]:
        """Run every sensor; returns (and remembers) all readings."""
        readings: List[SensorReading] = []
        for sensor in self.sensors:
            readings.extend(sensor.read(self, self.environment))
        self.last_readings = readings
        return readings

    # -- action ---------------------------------------------------------------

    def consider(self, action: str, source: str = "suggestion") -> EffectorCommand:
        """Wrap a suggested action into a command (no execution yet)."""
        return EffectorCommand(action=action, source=source)

    def can_execute(self, action: str) -> bool:
        """Safe AND an effector handles it?"""
        if not self.safety.is_safe(action):
            return False
        return any(e.handles(action) for e in self.effectors)

    def act(self, command: EffectorCommand) -> ActionResult:
        """Execute a command in the simulation (safety-gated)."""
        report = self.safety.validate_action(command.action)
        if not report.safe:
            self.actions_blocked += 1
            result = ActionResult(
                action=command.action, executed=False,
                position_before=self.position, position_after=self.position,
                blocked_reason="safety: " + "; ".join(report.violations),
                consequence="blocked by embodiment safety")
            self.last_result = result
            return result
        for effector in self.effectors:
            if effector.handles(command.action):
                result = effector.execute(command, self, self.environment)
                self.last_result = result
                if result.executed:
                    self.actions_executed += 1
                else:
                    self.actions_blocked += 1
                return result
        self.actions_blocked += 1
        result = ActionResult(action=command.action, executed=False,
                              position_before=self.position,
                              position_after=self.position,
                              blocked_reason="no effector handles this action")
        self.last_result = result
        return result

    # -- inspection -------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "SimulatedBody",
            "position": list(self.position),
            "energy": self.energy.snapshot(),
            "available_actions": list(ALLOWED_ACTIONS),
            "forbidden_actions": list(FORBIDDEN_ACTIONS),
            "sensors": [s.name for s in self.sensors],
            "effectors": [e.name for e in self.effectors],
            "actions_executed": self.actions_executed,
            "actions_blocked": self.actions_blocked,
            "last_readings": [r.payload for r in self.last_readings],
            "last_result": self.last_result.to_dict() if self.last_result else None,
            "safety": self.safety.snapshot(),
        }
