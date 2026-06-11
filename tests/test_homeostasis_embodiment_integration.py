"""Tests for homeostasis in the embodied (GridWorld) runner."""

from __future__ import annotations

from solaris_ai_nn.embodiment.simulation_runner import (
    SensorimotorSimulationRunner,
)
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator


def test_low_energy_suggests_rest():
    regulator = HomeostaticRegulator()
    regulator.update({"embodiment": {"energy": 0.8, "max_energy": 10.0,
                                     "exhausted": True}})
    best = regulator.synthesis.best()
    assert best.proposal in ("rest", "reduce_activity")
    assert "restore_energy" in best.source_needs


def test_danger_suggests_avoid():
    regulator = HomeostaticRegulator()
    regulator.update({"embodiment": {"energy": 8.0, "max_energy": 10.0,
                                     "exhausted": False,
                                     "dist_danger": 0.5}})
    best = regulator.synthesis.best()
    assert best.proposal in ("avoid_danger", "stabilize")


def test_reward_suggests_approach_only_if_safe():
    # Healthy and safe: approach_reward survives.
    safe = HomeostaticRegulator()
    safe.update({"embodiment": {"energy": 8.0, "max_energy": 10.0,
                                "exhausted": False, "dist_reward": 1.0}})
    proposals = {c.proposal for c in safe.synthesis.last_candidates
                 if not c.blocked}
    assert "approach_reward" in proposals
    # Exhausted: the same opportunity is suppressed with a reason.
    tired = HomeostaticRegulator()
    tired.update({"embodiment": {"energy": 0.5, "max_energy": 10.0,
                                 "exhausted": True, "dist_reward": 1.0}})
    blocked = {c.proposal: c for c in tired.synthesis.last_candidates
               if c.blocked}
    assert "approach_reward" in blocked
    assert blocked["approach_reward"].blocked_reason


def test_embodied_runner_with_homeostasis(tmp_path):
    runner = SensorimotorSimulationRunner(
        max_steps=120, seed=5, state_dir=str(tmp_path / "s"),
        enable_homeostasis=True, homeostasis_update_interval_steps=10)
    runner.run()
    regulator = runner.homeostasis
    assert regulator.updates >= 10
    # Body facts reached the variables (raw values preserved).
    energy = regulator.state.get("body_energy")
    assert energy is not None
    assert "raw_value" in energy.metadata
    assert (tmp_path / "s" / "homeostasis_state.json").exists()
    # The Inner MAP carries the summary.
    model = runner.observer.update()
    assert model.homeostasis is not None
    assert model.homeostasis["enabled"] is True


def test_blocked_actions_raise_boundary_pressure(tmp_path):
    runner = SensorimotorSimulationRunner(
        max_steps=150, seed=5, state_dir=str(tmp_path / "s"),
        enable_homeostasis=True, homeostasis_update_interval_steps=10)
    runner.run()
    blocked = sum(1 for r in runner.action_history if r.blocked_reason)
    if blocked:
        variable = runner.homeostasis.state.get("blocked_action_pressure")
        assert variable is not None and variable.value > 0
