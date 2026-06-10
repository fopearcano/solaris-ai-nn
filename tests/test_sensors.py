"""Tests for simulated sensors."""

from __future__ import annotations

from solaris_ai_nn.embodiment.body import SimulatedBody
from solaris_ai_nn.embodiment.grid_world import UNKNOWN, GridWorld
from solaris_ai_nn.embodiment.sensors import (
    AbsenceSensor,
    BoundarySensor,
    EnergySensor,
    ObjectSensor,
)

EMPTY = {"signal_source": 0, "obstacle": 0, "reward_marker": 0,
         "danger_marker": 0, "unknown_marker": 0}


def _world_body(**counts):
    cfg = {**EMPTY, **counts}
    world = GridWorld(width=7, height=7, seed=3, object_counts=cfg)
    return world, SimulatedBody(environment=world)


def test_boundary_sensor_emits_near_wall():
    world, body = _world_body()
    world.agent_pos = (0, 3)  # on the west wall
    readings = BoundarySensor().read(body, world)
    assert readings and readings[0].payload == "boundary"
    assert readings[0].intensity == 1.0
    world.agent_pos = (3, 3)  # centre: silent
    assert BoundarySensor().read(body, world) == []


def test_energy_sensor_emits_when_low():
    world, body = _world_body()
    assert EnergySensor().read(body, world) == []  # full energy: silent
    body.energy.energy = 2.0  # below low threshold
    readings = EnergySensor().read(body, world)
    assert readings and readings[0].payload == "low_energy"
    assert readings[0].modality == "internal"


def test_absence_sensor_emits_in_low_signal_state():
    world, body = _world_body()  # empty world: nothing to sense
    readings = AbsenceSensor().read(body, world)
    assert readings and readings[0].is_absence is True
    assert readings[0].payload == "I sense nothing"


def test_object_sensor_emits_novelty_for_unknown_marker():
    world, body = _world_body()
    world.objects[world.agent_pos] = UNKNOWN
    readings = ObjectSensor().read(body, world)
    payloads = [r.payload for r in readings]
    assert "on:unknown" in payloads
    novelty = [r for r in readings if r.kind == "MeaningEvent"]
    assert novelty and novelty[0].novelty > 0.5
