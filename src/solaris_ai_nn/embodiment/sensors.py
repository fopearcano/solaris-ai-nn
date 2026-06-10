"""Simulated sensors -- the body's only inputs, all from the grid world.

Each sensor reads (body, environment) and emits canonical-compatible
SensorReadings: proximity, on-object contact, boundary pressure, internal
energy need, absence (the Subtraction Principle embodied), and a clock tick.
Payload strings are short and stable so the event encoder's vocabulary can give
them collision-free slots.
"""

from __future__ import annotations

from typing import List

from .base import Body, Environment, Sensor, SensorReading
from .grid_world import DANGER, OBSTACLE, REWARD, SIGNAL, UNKNOWN

# Short payload names (encoder vocabulary friendly).
_NEAR = {SIGNAL: "near:signal", OBSTACLE: "near:obstacle", REWARD: "near:reward",
         DANGER: "near:danger", UNKNOWN: "near:unknown"}
_ON = {SIGNAL: "on:signal", REWARD: "on:reward", DANGER: "on:danger",
       UNKNOWN: "on:unknown"}

SENSOR_VOCABULARY = (list(_NEAR.values()) + list(_ON.values())
                     + ["boundary", "low_energy", "I sense nothing", "tick"])


class ProximitySensor(Sensor):
    """Emits a Stimulus for the nearest sensed object (intensity ~ closeness)."""

    name = "proximity"

    def read(self, body: Body, environment: Environment) -> List[SensorReading]:
        sense = environment.sense()
        if not sense["nearby"]:
            return []
        nearest = sense["nearby"][0]
        intensity = 1.0 / (1.0 + nearest["distance"])
        return [SensorReading(sensor=self.name,
                              payload=_NEAR.get(nearest["kind"], "near:unknown"),
                              intensity=round(intensity, 4), modality="proximity")]


class ObjectSensor(Sensor):
    """Emits contact Stimuli; unknown markers also raise a novelty MeaningEvent."""

    name = "object"

    def read(self, body: Body, environment: Environment) -> List[SensorReading]:
        on = environment.sense()["on_object"]
        if on is None:
            return []
        readings = [SensorReading(sensor=self.name, payload=_ON.get(on, "on:unknown"),
                                  intensity=0.9, modality="contact")]
        if on == UNKNOWN:
            readings.append(SensorReading(sensor=self.name, payload="unknown_object",
                                          kind="MeaningEvent", novelty=0.8))
        return readings


class BoundarySensor(Sensor):
    """High-intensity Stimulus when the body is at/next to a wall."""

    name = "boundary"

    def read(self, body: Body, environment: Environment) -> List[SensorReading]:
        d = environment.sense()["wall_distance"]
        if d > 1:
            return []
        intensity = 1.0 if d == 0 else 0.6
        return [SensorReading(sensor=self.name, payload="boundary",
                              intensity=intensity, modality="touch")]


class EnergySensor(Sensor):
    """Internal Stimulus when energy is low (intensity ~ deficit)."""

    name = "energy"

    def read(self, body: Body, environment: Environment) -> List[SensorReading]:
        model = body.energy
        if not model.is_low:
            return []
        deficit = 1.0 - (model.energy / max(model.max_energy, 1e-9))
        return [SensorReading(sensor=self.name, payload="low_energy",
                              intensity=round(min(1.0, deficit), 4),
                              modality="internal")]


class AbsenceSensor(Sensor):
    """Absence Stimulus when nothing meaningful is in sensing range."""

    name = "absence"

    def read(self, body: Body, environment: Environment) -> List[SensorReading]:
        if environment.sense()["any_signal"]:
            return []
        return [SensorReading(sensor=self.name, payload="I sense nothing",
                              intensity=0.4, is_absence=True, modality="internal")]


class ClockSensor(Sensor):
    """A low-intensity heartbeat tick every ``period`` reads (continuity)."""

    name = "clock"

    def __init__(self, period: int = 5) -> None:
        self.period = max(1, period)
        self._count = 0

    def read(self, body: Body, environment: Environment) -> List[SensorReading]:
        self._count += 1
        if self._count % self.period != 0:
            return []
        return [SensorReading(sensor=self.name, payload="tick", intensity=0.05,
                              modality="internal")]


def default_sensors() -> List[Sensor]:
    return [ProximitySensor(), ObjectSensor(), BoundarySensor(), EnergySensor(),
            AbsenceSensor(), ClockSensor()]
