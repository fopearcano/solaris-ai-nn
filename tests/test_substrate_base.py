"""Tests for the common substrate interface (BaseSubstrate + config)."""

from __future__ import annotations

import numpy as np
import pytest

from solaris_ai_nn.substrates.base import SubstrateConfig, SubstrateMetrics, SubstrateState
from solaris_ai_nn.substrates.registry import SubstrateRegistry

ALL = ["esn", "liquid_state", "spiking_recurrent"]


@pytest.mark.parametrize("name", ALL)
def test_interface_contract(name):
    sub = SubstrateRegistry.create(name, input_size=8, seed=3)
    assert sub.name == name
    assert sub.input_size == 8
    assert sub.state_size > 0
    assert sub.seed == 3

    out = sub.update(np.ones(8) * 0.5)
    assert isinstance(out, np.ndarray)
    assert out.shape == (sub.state_size,)

    state = sub.get_state()
    assert isinstance(state, np.ndarray)
    sub.set_state(state)

    snap = sub.snapshot()
    assert snap["name"] == name
    assert "config" in snap and "metrics" in snap

    metrics = sub.metrics()
    assert isinstance(metrics, SubstrateMetrics)
    assert metrics.updates == 1

    sub.reset()
    assert np.allclose(sub.get_state(), 0.0)


@pytest.mark.parametrize("name", ALL)
def test_rejects_wrong_input_size(name):
    sub = SubstrateRegistry.create(name, input_size=8, seed=1)
    with pytest.raises(ValueError):
        sub.update(np.ones(5))


def test_config_serialization_roundtrip():
    cfg = SubstrateConfig(name="liquid_state", input_size=8, state_size=32,
                          seed=4, params={"threshold": 0.8})
    back = SubstrateConfig.from_dict(cfg.to_dict())
    assert back == cfg
    assert back.params["threshold"] == 0.8


def test_substrate_state_to_dict():
    st = SubstrateState(vector=[1.0, 0.0], updates=3, extras={"membrane": [0.5, 0.1]})
    d = st.to_dict()
    assert d["vector"] == [1.0, 0.0]
    assert d["updates"] == 3
    assert d["extras"]["membrane"] == [0.5, 0.1]


@pytest.mark.parametrize("name", ALL)
def test_save_load_npz_roundtrip(name, tmp_path):
    a = SubstrateRegistry.create(name, input_size=6, seed=5)
    for i in range(12):
        a.update(np.ones(6) * (0.3 + 0.1 * (i % 3)))
    path = tmp_path / "state.npz"
    a.save_npz(path)

    b = SubstrateRegistry.create(name, input_size=6, seed=5)
    b.load_npz(path)
    assert np.array_equal(a.get_state(), b.get_state())
