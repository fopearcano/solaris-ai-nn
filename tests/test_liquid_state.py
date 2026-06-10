"""Tests for the LiquidStateSubstrate."""

from __future__ import annotations

import numpy as np

from solaris_ai_nn.substrates.liquid_state import LiquidStateSubstrate


def _strong_input(n: int) -> np.ndarray:
    return np.ones(n)


def test_updates_state():
    sub = LiquidStateSubstrate(input_size=8, state_size=48, seed=3)
    out = sub.update(_strong_input(8) * 0.5)
    assert out.shape == (48,)
    assert np.array_equal(out, sub.get_state())


def test_spike_like_activity_with_strong_input():
    sub = LiquidStateSubstrate(input_size=8, state_size=48, seed=3)
    for _ in range(20):
        sub.update(_strong_input(8))
    assert sub.spike_count > 0
    m = sub.metrics()
    assert m.spike_rate is not None and m.spike_rate > 0.0
    assert m.extras["average_activity"] > 0.0


def test_refractory_logic_does_not_crash():
    # Aggressive refractory period + constant strong drive: must stay bounded.
    sub = LiquidStateSubstrate(input_size=4, state_size=32, seed=1,
                               refractory_period=10, threshold=0.2)
    for _ in range(100):
        out = sub.update(_strong_input(4))
        assert np.all(np.isfinite(out))
    # Refractory counters never go negative.
    assert int(sub._refrac.min()) >= 0


def test_deterministic_with_seed():
    a = LiquidStateSubstrate(input_size=6, state_size=40, seed=9)
    b = LiquidStateSubstrate(input_size=6, state_size=40, seed=9)
    for i in range(25):
        u = np.ones(6) * (0.2 + 0.1 * (i % 4))
        a.update(u)
        b.update(u)
    assert np.array_equal(a.get_state(), b.get_state())
    assert a.spike_count == b.spike_count


def test_fading_memory_in_silence():
    sub = LiquidStateSubstrate(input_size=4, state_size=32, seed=2)
    for _ in range(10):
        sub.update(_strong_input(4))
    peak = float(np.linalg.norm(sub.get_state()))
    assert peak > 0.0
    # The trace decays once spikes stop driving it (zero input long enough).
    for _ in range(60):
        sub.update(np.zeros(4))
    assert float(np.linalg.norm(sub.get_state())) < peak


def test_full_persistence_includes_membrane(tmp_path):
    a = LiquidStateSubstrate(input_size=4, state_size=32, seed=5)
    for _ in range(10):
        a.update(_strong_input(4))
    path = tmp_path / "liquid.npz"
    a.save_npz(path)
    b = LiquidStateSubstrate(input_size=4, state_size=32, seed=5)
    b.load_npz(path)
    assert np.array_equal(a.get_state(), b.get_state())
    assert np.array_equal(a._membrane, b._membrane)
    assert np.array_equal(a._refrac, b._refrac)


def test_mutable_parameters_exposed():
    sub = LiquidStateSubstrate(input_size=4, state_size=16, seed=1)
    knobs = sub.mutable_parameters()
    assert "threshold" in knobs and "refractory_period" in knobs
    get, set_ = knobs["threshold"]
    set_(1.5)
    assert get() == 1.5
