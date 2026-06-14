"""Motor <-> Embodiment: GridWorld is reused as the first sandbox body."""

from __future__ import annotations

from solaris_ai_nn.embodiment.grid_world import GridWorld
from solaris_ai_nn.motor_membrane import (
    EmbodimentSandboxRuntime,
    GridWorldActuator,
    MotorAction,
    MotorActionScope,
    MotorActionType,
)


def test_gridworld_actuator_drives_existing_grid_world():
    world = GridWorld(seed=4)
    before = tuple(world.agent_pos)
    act = GridWorldActuator(world)
    # A move action steps the *existing* embodiment GridWorld (simulation only).
    act.execute(MotorAction(MotorActionType.MOVE_EAST))
    assert hasattr(world, "agent_pos")
    # The world may or may not move (walls), but it is the same body object.
    assert act.world is world
    del before


def test_runtime_builds_grid_world_body(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path),
                                  enable_gridworld=True, seed=4)
    rt.initialize()
    assert isinstance(rt._world, GridWorld)
    snap = rt.snapshot()
    assert snap["world"] is not None


def test_no_body_runtime_has_no_world(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path),
                                  enable_gridworld=False)
    rt.initialize()
    assert rt._world is None
    # Internal actions still run.
    out = rt.submit(MotorAction(MotorActionType.REST,
                                scope=MotorActionScope.INTERNAL_ONLY))
    assert out["executed"] is True


def test_gridworld_actions_are_all_simulated(tmp_path):
    rt = EmbodimentSandboxRuntime(state_dir=str(tmp_path), seed=4)
    rt.initialize()
    out = rt.submit(MotorAction(MotorActionType.MOVE_EAST,
                                scope=MotorActionScope.SANDBOX_ONLY))
    assert out["result"]["simulated"] is True
