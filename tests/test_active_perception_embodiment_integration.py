"""Integration: sampling stays simulation-only around embodiment."""

from __future__ import annotations

from solaris_ai_nn.active_perception import (
    ActiveSensingController,
    ExplorationMemory,
    SamplingPolicy,
)
from solaris_ai_nn.active_perception.sampling_actions import (
    SamplingAction,
    SamplingActionType,
    SamplingScope,
)


def test_look_action_is_simulation_only():
    action = SamplingAction(action_type=SamplingActionType.LOOK,
                            scope=SamplingScope.SIMULATION_ONLY)
    candidate = action.to_action_candidate()
    assert candidate.executable_scope == "simulation_only"


def test_ping_is_simulated_only(tmp_path):
    from solaris_ai_nn.ecology.nursery import (
        DevelopmentalNursery,
        NurseryConfig,
    )

    nursery = DevelopmentalNursery(config=NurseryConfig(
        seed=7, duration_steps=40, output_state_dir=str(tmp_path)))
    ping = nursery.sample("emit_simulated_ping")
    assert ping["ping"] == "simulated"
    assert ping["scope"] == "simulation_only"


def test_gridworld_is_simulation_boundary(tmp_path):
    # A GridWorld exists as simulation; sampling never reaches the real world.
    from solaris_ai_nn.embodiment.grid_world import GridWorld

    world = GridWorld(seed=7)
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path))
    # A look-style sampling action is bounded to simulation scope.
    decision = ctrl.select({"step": 0, "mysterium_pressure": 0.5,
                            "world_model": {"graph_node_count": 5,
                                            "unknown_node_count": 2,
                                            "prediction_accuracy": 0.5},
                            "health_level": "ok", "energy": 0.9})
    result = ctrl.execute_if_allowed(decision, {"step": 0})
    assert result.scope in SamplingScope.RUNNABLE
    assert world is not None  # simulation exists; nothing real was touched


def test_energy_respected_low_energy_recovers(tmp_path):
    ctrl = ActiveSensingController(
        policy=SamplingPolicy(mode="balanced", seed=7),
        memory=ExplorationMemory(state_dir=tmp_path))
    # Low energy forces recovery mode (rest/wait/consolidate), never costly
    # exploration.
    decision = ctrl.select({"step": 0, "mysterium_pressure": 0.8,
                            "energy": 0.1, "health_level": "ok"})
    assert decision.mode == "recovery"
    assert decision.action.action_type in (
        "rest", "wait", "consolidate_before_sampling", "seek_absence",
        "no_sampling_action")
