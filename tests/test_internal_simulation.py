"""InternalSimulation: bounded; marked non-real; not observation."""

from __future__ import annotations

from solaris_ai_nn.sensorium_cognition import (
    InternalSimulation,
    SimulationScope,
)


def test_simulation_bounded():
    sim = InternalSimulation(max_steps=3)
    result = sim.simulate_sequence(
        ["s1", "s2", "s3", "s4", "s5"], SimulationScope.SIGN_SEQUENCE)
    assert len(result.steps) == 3  # capped at max_steps


def test_simulation_marked_non_real():
    result = InternalSimulation().simulate_sequence(
        ["s1", "s2"], SimulationScope.SIGN_SEQUENCE)
    d = result.to_dict()
    assert d["is_real_observation"] is False
    assert d["simulated"] is True
    assert all(s["simulated"] for s in d["steps"])


def test_simulation_not_observation():
    result = InternalSimulation().simulate_absence("s1")
    assert result.is_real_observation is False
    assert "NOT a real observation" in result.to_dict()["note"]


def test_simulation_seeds_hypothesis():
    result = InternalSimulation().simulate_sequence(
        ["s1", "s2"], SimulationScope.SIGN_SEQUENCE)
    assert result.seeds_hypothesis is True
    assert result.usefulness > 0.0
