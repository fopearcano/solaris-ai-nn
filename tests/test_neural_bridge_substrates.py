"""Tests for the bridge running on each selectable substrate."""

from __future__ import annotations

import pytest

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.signals import canonical as C
from solaris_ai_nn.signals.encoding import EventEncoder

ALL = ["esn", "liquid_state", "spiking_recurrent"]


def _bridge(name: str) -> SolarisNeuralBridge:
    return SolarisNeuralBridge(
        action_labels=["approach", "withdraw", "consume"],
        encoder=EventEncoder(vocabulary=["light", "noise", "food"]),
        substrate_name=name, seed=3)


@pytest.mark.parametrize("name", ALL)
def test_bridge_processes_and_learns(name):
    bridge = _bridge(name)
    result = bridge.process(C.Stimulus(payload="light", intensity=0.7))
    assert result["substrate"] == name
    assert result["suggested_action"] in bridge.action_labels
    assert result["reservoir_energy"] >= 0.0
    # Reaction feedback reaches the readout regardless of substrate.
    before = [row[:] for row in bridge.readout.weights]
    bridge.react(C.Reaction(valence=1.0))
    assert bridge.readout.weights != before
    assert bridge.telemetry.readout_updates == 1


@pytest.mark.parametrize("name", ALL)
def test_bridge_snapshot_includes_substrate_info(name):
    bridge = _bridge(name)
    bridge.process(C.Stimulus(payload="noise", intensity=0.5))
    snap = bridge.snapshot()
    assert snap["substrate_type"] == name
    assert snap["substrate_config"]["name"] == name
    assert "state_norm" in snap["substrate_metrics"]
    assert "activity_rate" in snap["substrate_metrics"]
    assert snap["substrate_state_norm"] >= 0.0


def test_default_substrate_is_esn_with_back_compat():
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=1)
    assert bridge.substrate.name == "esn"
    assert bridge.esn is not None  # legacy accessor still alive
    bridge.process(C.Stimulus(payload="x", intensity=0.4))
    # bridge.esn and the substrate are the same object's state.
    assert list(bridge.esn.state) == [float(v) for v in bridge.substrate.get_state()]


def test_non_esn_bridges_have_no_esn_attr():
    bridge = _bridge("liquid_state")
    assert bridge.esn is None
    assert bridge.substrate.name == "liquid_state"


def test_substrate_config_passthrough():
    bridge = SolarisNeuralBridge(
        action_labels=["a", "b"], substrate_name="spiking_recurrent",
        substrate_config={"state_size": 48, "threshold": 0.8}, seed=2)
    assert bridge.substrate.state_size == 48
    assert bridge.substrate.params["threshold"] == 0.8
    assert bridge.readout.n_features == 49  # state + bias


def test_explicit_substrate_instance():
    from solaris_ai_nn.substrates.registry import SubstrateRegistry

    enc = EventEncoder()
    sub = SubstrateRegistry.create("liquid_state", input_size=enc.dim, seed=4)
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], encoder=enc, substrate=sub)
    assert bridge.substrate is sub
    bridge.process(C.Stimulus(payload="y", intensity=0.6))
