"""AffordanceDetector: gridworld is manipulable in sim; sensory is observe-only."""

from __future__ import annotations

from solaris_ai_nn.embodiment.grid_world import GridWorld
from solaris_ai_nn.motor_membrane import (
    AffordanceDetector,
    AffordanceType,
    MotorActionScope,
)


def test_gridworld_affordances_are_manipulable_in_simulation():
    amap = AffordanceDetector().detect(grid_world=GridWorld(seed=5))
    targets = amap.manipulable_targets()
    assert "gridworld:agent" in targets


def test_sensory_sources_are_observable_only():
    amap = AffordanceDetector().detect(
        sensory_sources=[{"source_id": "s1"}, {"source_id": "s2"}])
    sensory = [a for a in amap.affordances
               if a.target_ref.startswith("sensory:")]
    assert sensory
    for a in sensory:
        assert a.manipulable is False
        assert a.affordance_type == AffordanceType.OBSERVABLE
        assert a.target_ref not in amap.manipulable_targets()


def test_world_model_nodes_are_inspectable():
    amap = AffordanceDetector().detect(world_model_nodes=["a", "b"])
    wm = [a for a in amap.affordances if a.target_ref.startswith("wm:")]
    assert wm
    assert all(a.scope == MotorActionScope.SIMULATION_ONLY for a in wm)


def test_forbidden_real_world_target():
    a = AffordanceDetector().forbidden_target("/dev/ttyUSB0")
    assert a.affordance_type == AffordanceType.FORBIDDEN_REAL_WORLD
    assert a.scope == MotorActionScope.FORBIDDEN_REAL_WORLD
    assert a.manipulable is False
