"""Tests for explicit, checkpointed, rollbackable substrate switching."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.plasticity.mutation import PlasticityChange, PlasticityStep, PlasticityTarget
from solaris_ai_nn.plasticity.safety import PlasticitySafetyValidator
from solaris_ai_nn.signals import canonical as C
from solaris_ai_nn.substrates.registry import SubstrateRegistry
from solaris_ai_nn.substrates.switching import SubstrateSwitcher


def _driven_substrate(name="liquid_state", seed=3):
    sub = SubstrateRegistry.create(name, input_size=6, seed=seed)
    for _ in range(12):
        sub.update(np.ones(6) * 0.7)
    return sub


def test_automatic_switching_is_not_allowed(tmp_path):
    sw = SubstrateSwitcher(state_dir=tmp_path / "sw")
    sub = _driven_substrate()
    with pytest.raises(PermissionError):
        sw.switch(sub, "spiking_recurrent")  # no explicit=True


def test_policy_cannot_switch_substrate_via_plasticity():
    """The safety validator rejects any substrate-switch mutation outright."""
    v = PlasticitySafetyValidator()
    step = PlasticityStep(
        target=PlasticityTarget("substrate", "substrate_name"),
        change=PlasticityChange(old_value="esn", new_value="liquid_state"))
    assert not v.is_safe(step)
    assert "may not be mutated" in v.explain_rejection(step)


def test_explicit_switch_checkpoints_old_state(tmp_path):
    sw = SubstrateSwitcher(state_dir=tmp_path / "sw")
    old = _driven_substrate("liquid_state")
    old_state = old.get_state().copy()

    new = sw.switch(old, "spiking_recurrent", explicit=True)
    assert new.name == "spiking_recurrent"
    record = sw.history[-1]
    # Old state was saved BEFORE the switch (never discarded).
    assert Path(record.old_checkpoint).exists()
    assert Path(record.new_checkpoint).exists()
    # Same dimensions here -> state transferred (binarised by the spiking sub).
    assert record.state_transferred is True
    # The checkpoint really holds the old state.
    restored = SubstrateRegistry.create("liquid_state", input_size=6, seed=3)
    restored.load_npz(record.old_checkpoint)
    assert np.array_equal(restored.get_state(), old_state)


def test_rollback_switch_restores_previous_substrate(tmp_path):
    sw = SubstrateSwitcher(state_dir=tmp_path / "sw")
    old = _driven_substrate("liquid_state")
    old_state = old.get_state().copy()
    sw.switch(old, "spiking_recurrent", explicit=True)

    back = sw.rollback_switch()
    assert back.name == "liquid_state"
    assert back.state_size == old.state_size
    assert np.array_equal(back.get_state(), old_state)
    assert sw.history[-1].rolled_back is True
    # Nothing left to roll back now.
    with pytest.raises(ValueError):
        sw.rollback_switch()


def test_incompatible_sizes_initialise_safely(tmp_path):
    sw = SubstrateSwitcher(state_dir=tmp_path / "sw")
    old = _driven_substrate("liquid_state")  # state_size 96
    new = sw.switch(old, "esn", {"state_size": 32}, explicit=True)
    assert new.state_size == 32
    assert sw.history[-1].state_transferred is False
    assert np.allclose(new.get_state(), 0.0)  # safe zero start


def test_switch_updates_bridge_and_history(tmp_path):
    bridge = SolarisNeuralBridge(action_labels=["a", "b"],
                                 substrate_name="liquid_state", seed=2)
    bridge.process(C.Stimulus(payload="x", intensity=0.5))
    sw = SubstrateSwitcher(state_dir=tmp_path / "sw", bridge=bridge)
    sw.switch(bridge.substrate, "spiking_recurrent", explicit=True)
    assert bridge.substrate.name == "spiking_recurrent"
    assert len(bridge.substrate_switches) == 1
    # The bridge keeps working after the switch.
    result = bridge.process(C.Stimulus(payload="y", intensity=0.5))
    assert result["substrate"] == "spiking_recurrent"
    # Switch history reaches the Inner MAP via the observer.
    from solaris_ai_nn.inner_map.observer import InnerMapObserver
    model = InnerMapObserver(bridge=bridge).update()
    assert len(model.neural.substrate_switch_history) == 1
