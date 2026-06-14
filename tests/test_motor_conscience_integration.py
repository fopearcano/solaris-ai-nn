"""Motor <-> Conscience: spine phase, gated submit, bounded profiles."""

from __future__ import annotations

from solaris_ai_nn.conscience import (
    ConscienceOrchestrator,
    RunContext,
    RunMode,
    ScenarioProfileRegistry,
)
from solaris_ai_nn.conscience.spine import SpinePhase


def test_motor_phase_in_spine_order():
    order = SpinePhase.ORDER
    assert SpinePhase.MOTOR_ACTION_FIREWALL in order
    assert order.index(SpinePhase.SAFETY_GOVERNANCE_VALIDATION) \
        < order.index(SpinePhase.MOTOR_ACTION_FIREWALL) \
        < order.index(SpinePhase.ACTION_SUGGESTION)


def _ctx(tmp_path, **meta):
    return RunContext(
        mode=RunMode.SHORT_DEMO, state_dir=str(tmp_path / "state"),
        max_steps=8,
        enabled_modules=["bridge", "ecology", "governance", "ops", "executive",
                         "motor_membrane"],
        metadata=meta)


def test_motor_profile_runs_bounded(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path, motor_profile_id="gridworld_minimal"))
    orch.initialize()
    orch.run()
    assert orch.step_count == 8
    assert orch.counts.get("motor_action", 0) > 0
    assert "motor_membrane" not in orch.summary()["degraded_modules"]


def test_motor_runtime_never_has_real_world_authority(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path))
    orch.initialize()
    orch.run()
    membrane = orch.components.get("motor_membrane")
    assert membrane.summary()["real_world_authority"] is False
    assert membrane.firewall.enabled is True


def test_bus_receives_motor_safety_event(tmp_path):
    orch = ConscienceOrchestrator()
    orch.configure(_ctx(tmp_path))
    orch.initialize()
    received = []
    orch.bus.subscribe(
        "safety_event",
        lambda m: received.append(m) if m.source_module == "motor_membrane"
        else None, "t")
    orch.run()
    assert received  # the membrane published motor status to the bus


def test_motor_scenario_profiles_exist():
    ids = set(ScenarioProfileRegistry().ids())
    assert {"pilot3_plan_only", "motor_firewall_preflight",
            "dry_run_motor_trace", "gridworld_motor_short",
            "gridworld_reward_danger_short",
            "mixed_sensory_gridworld_short"} <= ids
