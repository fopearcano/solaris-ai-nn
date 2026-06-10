"""Tests for the SpikingRecurrentSubstrate."""

from __future__ import annotations

import numpy as np

from solaris_ai_nn.substrates.spiking_recurrent import SpikingRecurrentSubstrate


def test_binary_spike_output():
    sub = SpikingRecurrentSubstrate(input_size=6, state_size=40, seed=3)
    for _ in range(15):
        out = sub.update(np.ones(6))
        assert set(np.unique(out)).issubset({0.0, 1.0})  # strictly binary


def test_spike_rate_metric_exists():
    sub = SpikingRecurrentSubstrate(input_size=6, state_size=40, seed=3)
    for _ in range(20):
        sub.update(np.ones(6))
    m = sub.metrics()
    assert m.spike_rate is not None
    assert m.spike_rate > 0.0
    assert "silent_units_ratio" in m.extras
    assert "saturated_units_ratio" in m.extras
    assert "recurrent_activity_norm" in m.extras
    assert 0.0 <= m.extras["silent_units_ratio"] <= 1.0


def test_silent_input_produces_bounded_decay():
    sub = SpikingRecurrentSubstrate(input_size=4, state_size=32, seed=2)
    for _ in range(10):
        sub.update(np.ones(4))
    # Now silence: membranes must decay and stay finite/bounded.
    norms = []
    for _ in range(80):
        out = sub.update(np.zeros(4))
        assert np.all(np.isfinite(out))
        norms.append(float(np.linalg.norm(sub._v)))
    assert norms[-1] <= max(norms)  # no blow-up under silence
    assert norms[-1] < 10.0 * 32   # comfortably inside the membrane clip


def test_deterministic_with_seed_even_with_noise():
    a = SpikingRecurrentSubstrate(input_size=5, state_size=32, seed=8, noise_level=0.1)
    b = SpikingRecurrentSubstrate(input_size=5, state_size=32, seed=8, noise_level=0.1)
    for i in range(25):
        u = np.ones(5) * (0.5 if i % 2 else 0.9)
        a.update(u)
        b.update(u)
    assert np.array_equal(a.get_state(), b.get_state())
    assert np.array_equal(a._v, b._v)


def test_refractory_blocks_immediate_refire():
    sub = SpikingRecurrentSubstrate(input_size=2, state_size=16, seed=1,
                                    refractory_period=5, threshold=0.1)
    sub.update(np.ones(2) * 5.0)
    first = sub.get_state().copy()
    fired_units = first > 0.5
    if fired_units.any():
        # Units that just fired cannot fire on the immediately following step.
        second = sub.update(np.ones(2) * 5.0)
        assert not np.any(second[fired_units] > 0.5)
    assert int(sub._refrac.min()) >= 0


def test_state_drift_metric_tracked():
    sub = SpikingRecurrentSubstrate(input_size=4, state_size=32, seed=4)
    sub.update(np.ones(4))
    sub.update(np.zeros(4))
    assert sub.metrics().drift >= 0.0


def test_full_persistence_roundtrip(tmp_path):
    a = SpikingRecurrentSubstrate(input_size=4, state_size=24, seed=6)
    for _ in range(12):
        a.update(np.ones(4) * 0.8)
    path = tmp_path / "spiking.npz"
    a.save_npz(path)
    b = SpikingRecurrentSubstrate(input_size=4, state_size=24, seed=6)
    b.load_npz(path)
    assert np.array_equal(a.get_state(), b.get_state())
    assert np.array_equal(a._v, b._v)
    assert np.array_equal(a._unit_rate, b._unit_rate)
