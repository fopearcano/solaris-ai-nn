"""Tests for homeostatic modulation inside the NeuralBridge."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator
from solaris_ai_nn.signals import canonical as C


def _regulator_with_energy_need():
    regulator = HomeostaticRegulator()
    regulator.update({"embodiment": {"energy": 0.5, "max_energy": 10.0,
                                     "exhausted": True}})
    return regulator


def test_bridge_with_homeostasis_biases_suggestions():
    regulator = _regulator_with_energy_need()
    labels = ["rest", "explore_safely"]
    biased = SolarisNeuralBridge(action_labels=labels, seed=3,
                                 exploration=0.0,
                                 enable_homeostasis=True,
                                 homeostatic_regulator=regulator)
    plain = SolarisNeuralBridge(action_labels=labels, seed=3,
                                exploration=0.0)
    rest_votes_biased = 0
    rest_votes_plain = 0
    for i in range(20):
        stim = C.Stimulus(payload=f"p{i % 2}", intensity=0.5)
        if biased.process(stim)["suggested_action"] == "rest":
            rest_votes_biased += 1
        if plain.process(stim)["suggested_action"] == "rest":
            rest_votes_plain += 1
    # The energy drive's rest bias tilts the suggestion distribution.
    assert rest_votes_biased >= rest_votes_plain


def test_bridge_still_does_not_commit_actions():
    regulator = _regulator_with_energy_need()
    bridge = SolarisNeuralBridge(action_labels=["rest", "look"], seed=3,
                                 enable_homeostasis=True,
                                 homeostatic_regulator=regulator)
    bridge.process(C.Stimulus(payload="x", intensity=0.5))
    suggestion = bridge.last_suggestion()
    assert suggestion["committed"] is False  # the invariant survives


def test_snapshot_includes_homeostasis():
    regulator = _regulator_with_energy_need()
    bridge = SolarisNeuralBridge(action_labels=["rest", "look"], seed=3,
                                 enable_homeostasis=True,
                                 homeostatic_regulator=regulator)
    bridge.process(C.Stimulus(payload="x", intensity=0.5))
    snap = bridge.snapshot()
    assert snap["homeostasis"]["dominant_need"] == "restore_energy"
    # Disabled bridges carry no homeostasis key.
    plain = SolarisNeuralBridge(action_labels=["a"], seed=3)
    plain.process(C.Stimulus(payload="x"))
    assert "homeostasis" not in plain.snapshot()


def test_suppressed_proposals_carry_no_bias():
    regulator = HomeostaticRegulator()
    regulator.update({"embodiment": {
        "energy": 0.5, "max_energy": 10.0, "exhausted": True,
        "dist_reward": 1.0}})
    bias = regulator.to_desire_bias()
    # approach_reward was suppressed by the energy conflict: zero bias.
    assert "approach_reward" not in bias
    assert bias.get("rest", 0) > 0
