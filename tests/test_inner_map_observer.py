"""Tests for the InnerMapObserver (read-only observation)."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.signals import canonical as C
from solaris_ai_nn.signals.encoding import EventEncoder


def _bridge(seed: int = 3) -> SolarisNeuralBridge:
    b = SolarisNeuralBridge(
        action_labels=["approach", "withdraw", "consume"],
        encoder=EventEncoder(vocabulary=["light", "noise", "food", "I exist!"]),
        seed=seed,
    )
    world = {"light": "approach", "noise": "withdraw", "food": "consume"}
    for p in ("light", "noise", "food", "light"):
        r = b.process(C.Stimulus(payload=p, intensity=0.6, origin="world"))
        b.react(C.Reaction(valence=1.0 if r["suggested_action"] == world[p] else -1.0))
    return b


def test_observer_inspects_bridge():
    b = _bridge()
    obs = InnerMapObserver(bridge=b)
    out = obs.observe_bridge(b)
    assert "neural" in out and "tendencies" in out and "modules" in out
    assert out["neural"]["reservoir_size"] == b.esn.n_reservoir
    assert out["neural"]["input_vector_size"] == b.encoder.dim


def test_observer_update_returns_model():
    b = _bridge()
    obs = InnerMapObserver(bridge=b)
    model = obs.update()
    assert isinstance(model, InnerMapModel)
    assert model.neural.reservoir_size > 0
    assert model.plasticity.habit_pathways > 0


def test_observer_snapshot_is_dict():
    b = _bridge()
    obs = InnerMapObserver(bridge=b)
    snap = obs.snapshot()
    assert isinstance(snap, dict)
    assert "neural" in snap and "memory" in snap and "boundaries" in snap


def test_observer_does_not_mutate_bridge():
    b = _bridge()
    state_before = list(b.esn.state)
    steps_before = b.telemetry.steps
    readout_before = [row[:] for row in b.readout.weights]

    obs = InnerMapObserver(bridge=b)
    obs.update()
    obs.snapshot()
    obs.observe_bridge(b)

    assert b.esn.state == state_before
    assert b.telemetry.steps == steps_before
    assert b.readout.weights == readout_before


def test_observe_memory_consolidates():
    b = _bridge()
    obs = InnerMapObserver(bridge=b)
    out = obs.observe_memory(b.trace)
    assert "memory" in out and "report" in out
    assert out["memory"]["recent_reaction_count"] >= 1
