"""Tests for the SolarisNeuralBridge compatibility layer."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.signals import canonical as C


def _bridge() -> SolarisNeuralBridge:
    return SolarisNeuralBridge(action_labels=["approach", "withdraw", "consume"], seed=3)


def test_bridge_processes_stimulus():
    bridge = _bridge()
    result = bridge.process(C.Stimulus(payload="light", intensity=0.7))
    assert result["input_type"] == "Stimulus"
    assert result["suggested_action"] in bridge.action_labels
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["reservoir_energy"] >= 0.0
    assert set(result["scores"].keys()) == set(bridge.action_labels)


def test_bridge_processes_push():
    bridge = _bridge()
    result = bridge.process({"kind": "Push", "intensity": 0.4, "direction": "reactive"})
    assert result["input_type"] == "Push"


def test_bridge_processes_logos_and_sets_modulation_state():
    bridge = _bridge()
    result = bridge.process(C.LogosTension(division=0.6, union=0.3))
    assert result["input_type"] == "LogosTension"
    assert abs(result["logos_fracture"] - 0.3) < 1e-9
    # Subsequent signals now see the stored LogosTension.
    snap = bridge.snapshot()
    assert snap["logos"] is not None
    assert snap["logos"]["division"] == 0.6


def test_bridge_suggests_action_and_desire():
    bridge = _bridge()
    assert bridge.suggest_action() is None  # nothing processed yet
    assert bridge.suggest_desire() is None
    bridge.process(C.Stimulus(payload="light", intensity=0.5))
    action = bridge.suggest_action()
    desire = bridge.suggest_desire()
    assert isinstance(action, C.Action)
    assert isinstance(desire, C.Desire)
    assert action.name == desire.proposal


def test_bridge_updates_from_reaction():
    bridge = _bridge()
    bridge.process(C.Stimulus(payload="light", intensity=0.6))
    chosen = bridge._last_chosen
    before = [row[:] for row in bridge.readout.weights]
    bridge.react(C.Reaction(valence=1.0))
    after = bridge.readout.weights
    # The chosen action's readout row must have changed.
    assert after[chosen] != before[chosen]
    assert bridge.telemetry.readout_updates == 1


def test_bridge_react_accepts_dict():
    bridge = _bridge()
    bridge.process(C.Stimulus(payload="food", intensity=0.6))
    bridge.react({"kind": "Reaction", "valence": -1.0})
    assert bridge.telemetry.readout_updates == 1
    assert len(bridge.habit.weights) >= 1


def test_bridge_react_before_process_is_noop():
    bridge = _bridge()
    bridge.react(C.Reaction(valence=1.0))  # must not raise
    assert bridge.telemetry.readout_updates == 0


def test_bridge_process_many_and_snapshot():
    bridge = _bridge()
    signals = [C.Stimulus(payload=p, intensity=0.5) for p in ("light", "noise", "food")]
    results = bridge.process_many(signals)
    assert len(results) == 3
    snap = bridge.snapshot()
    assert snap["steps"] == 3
    assert "telemetry" in snap
    assert snap["reservoir_energy"] >= 0.0
