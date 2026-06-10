"""Tests for generic substrate persistence (npz + manifest)."""

from __future__ import annotations

import numpy as np

from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.runtime.persistence import PersistenceManager
from solaris_ai_nn.substrates.registry import SubstrateRegistry


def test_saves_substrate_state(tmp_path):
    pm = PersistenceManager(tmp_path / "state")
    sub = SubstrateRegistry.create("liquid_state", input_size=6, seed=3)
    for _ in range(10):
        sub.update(np.ones(6) * 0.6)
    pm.save_substrate(sub, step=10)
    assert pm.substrate_state_path.exists()
    assert pm.substrate_manifest_path.exists()


def test_manifest_includes_name_and_config(tmp_path):
    pm = PersistenceManager(tmp_path / "state")
    sub = SubstrateRegistry.create("spiking_recurrent", input_size=6, seed=4)
    sub.update(np.ones(6))
    pm.save_substrate(sub, step=7)
    manifest = pm.load_substrate_manifest()
    assert manifest["substrate"] == "spiking_recurrent"
    assert manifest["config"]["name"] == "spiking_recurrent"
    assert manifest["state_size"] == sub.state_size
    assert manifest["input_size"] == 6
    assert manifest["seed"] == 4
    assert manifest["last_saved_step"] == 7


def test_loads_substrate_state(tmp_path):
    pm = PersistenceManager(tmp_path / "state")
    src = SubstrateRegistry.create("liquid_state", input_size=6, seed=5)
    for _ in range(15):
        src.update(np.ones(6) * 0.8)
    pm.save_substrate(src, step=15)

    dst = SubstrateRegistry.create("liquid_state", input_size=6, seed=5)
    assert pm.load_substrate_into(dst) is True
    assert np.array_equal(src.get_state(), dst.get_state())
    assert np.array_equal(src._membrane, dst._membrane)  # full fidelity


def test_load_refuses_mismatched_substrate(tmp_path):
    pm = PersistenceManager(tmp_path / "state")
    src = SubstrateRegistry.create("liquid_state", input_size=6, seed=5)
    src.update(np.ones(6))
    pm.save_substrate(src)
    other = SubstrateRegistry.create("spiking_recurrent", input_size=6, seed=5)
    assert pm.load_substrate_into(other) is False  # name mismatch -> not loaded


def test_runner_checkpoints_substrate_files(tmp_path):
    runner = ContinuousRunner(
        state_dir=tmp_path / "brain", max_steps=40, checkpoint_interval_steps=20,
        substrate_name="spiking_recurrent")
    runner.run()
    assert runner.pm.substrate_state_path.exists()
    manifest = runner.pm.load_substrate_manifest()
    assert manifest["substrate"] == "spiking_recurrent"


def test_esn_checkpoint_backward_compat(tmp_path):
    """The original ESN checkpoint path still restores across a restart."""
    state_dir = tmp_path / "brain"
    r1 = ContinuousRunner(state_dir=state_dir, max_steps=30, seed=7)
    r1.run()
    end_state = list(r1.bridge.esn.state)
    r2 = ContinuousRunner(state_dir=state_dir, max_steps=10, seed=7)
    assert list(r2.bridge.esn.state) == end_state
