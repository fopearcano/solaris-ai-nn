"""Tests for the executive inside the NeuralBridge."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator
from solaris_ai_nn.signals import canonical as C


def _regulator_pressing_rest():
    regulator = HomeostaticRegulator()
    regulator.update({"embodiment": {"energy": 0.5, "max_energy": 10.0,
                                     "exhausted": True}})
    return regulator


def test_bridge_with_executive_selects_final_suggestion():
    regulator = _regulator_pressing_rest()
    bridge = SolarisNeuralBridge(
        action_labels=["rest", "look"], seed=3, exploration=0.0,
        enable_homeostasis=True, homeostatic_regulator=regulator,
        enable_executive=True)
    result = bridge.process(C.Stimulus(payload="x", intensity=0.5))
    assert "executive_selection" in result
    # The energy pressure makes rest the arbitrated suggestion.
    assert result["executive_selection"] in ("rest", "reduce_activity",
                                             "stabilize")
    if result["executive_selection"] in bridge.action_labels:
        assert result["suggested_action"] == result["executive_selection"]
    assert bridge.executive_layer.decisions >= 1


def test_disabled_behavior_unchanged():
    plain = SolarisNeuralBridge(action_labels=["a", "b"], seed=3)
    enabled = SolarisNeuralBridge(action_labels=["a", "b"], seed=3)
    for i in range(10):
        stim = C.Stimulus(payload=f"p{i % 2}", intensity=0.5)
        r1 = plain.process(stim)
        r2 = enabled.process(C.Stimulus(payload=f"p{i % 2}",
                                        intensity=0.5))
        assert r1["suggested_action"] == r2["suggested_action"]
        assert "executive_selection" not in r1
    assert plain.executive_layer is None


def test_suggestions_are_not_committed():
    regulator = _regulator_pressing_rest()
    bridge = SolarisNeuralBridge(
        action_labels=["rest", "look"], seed=3,
        enable_homeostasis=True, homeostatic_regulator=regulator,
        enable_executive=True)
    bridge.process(C.Stimulus(payload="x", intensity=0.5))
    suggestion = bridge.last_suggestion()
    assert suggestion["committed"] is False
    selected = bridge.executive_layer.last_result.selected
    assert selected.committed is False


def test_snapshot_includes_executive():
    bridge = SolarisNeuralBridge(action_labels=["rest", "look"], seed=3,
                                 enable_executive=True)
    bridge.process(C.Stimulus(payload="x", intensity=0.5))
    snap = bridge.snapshot()
    assert snap["executive"]["enabled"] is True
    assert snap["executive"]["mode"] == "arbitrated"
    plain = SolarisNeuralBridge(action_labels=["a"], seed=3)
    plain.process(C.Stimulus(payload="x"))
    assert "executive" not in plain.snapshot()
