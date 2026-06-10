"""Tests for the SubstrateRegistry."""

from __future__ import annotations

import pytest

from solaris_ai_nn.substrates.base import BaseSubstrate
from solaris_ai_nn.substrates.esn_substrate import EchoStateSubstrate
from solaris_ai_nn.substrates.liquid_state import LiquidStateSubstrate
from solaris_ai_nn.substrates.registry import SubstrateRegistry
from solaris_ai_nn.substrates.spiking_recurrent import SpikingRecurrentSubstrate


def test_lists_required_substrates():
    names = SubstrateRegistry.list_substrates()
    assert "esn" in names
    assert "liquid_state" in names
    assert "spiking_recurrent" in names


def test_creates_each_by_name():
    assert isinstance(SubstrateRegistry.create("esn", input_size=4), EchoStateSubstrate)
    assert isinstance(SubstrateRegistry.create("liquid_state", input_size=4),
                      LiquidStateSubstrate)
    assert isinstance(SubstrateRegistry.create("spiking_recurrent", input_size=4),
                      SpikingRecurrentSubstrate)


def test_rejects_unknown_substrate():
    with pytest.raises(ValueError):
        SubstrateRegistry.create("transformer", input_size=4)
    with pytest.raises(ValueError):
        SubstrateRegistry.default_config("nope", input_size=4)


def test_validate_config():
    cfg = SubstrateRegistry.validate_config("esn", {"state_size": "32", "seed": 1})
    assert cfg["state_size"] == 32  # normalised to int
    with pytest.raises(ValueError):
        SubstrateRegistry.validate_config("esn", {"state_size": 0})
    with pytest.raises(ValueError):
        SubstrateRegistry.validate_config("unknown", {})


def test_default_configs():
    cfg = SubstrateRegistry.default_config("liquid_state", input_size=10, seed=2)
    assert cfg.name == "liquid_state"
    assert cfg.input_size == 10
    assert cfg.state_size > 0
    assert cfg.seed == 2


def test_create_from_config_roundtrip():
    cfg = SubstrateRegistry.default_config("spiking_recurrent", input_size=6, seed=9)
    sub = SubstrateRegistry.create_from_config(cfg)
    assert sub.name == "spiking_recurrent"
    assert sub.input_size == 6
    assert sub.seed == 9


def test_register_requires_base_subclass():
    with pytest.raises(TypeError):
        SubstrateRegistry.register("bad", dict)  # type: ignore[arg-type]
    assert issubclass(SubstrateRegistry._classes["esn"], BaseSubstrate)
