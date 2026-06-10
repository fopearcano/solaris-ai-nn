"""Tests for the EchoStateSubstrate wrapper."""

from __future__ import annotations

import numpy as np

from solaris_ai_nn.reservoir.esn import ESN
from solaris_ai_nn.substrates.esn_substrate import EchoStateSubstrate


def test_wrapper_updates_state():
    sub = EchoStateSubstrate(input_size=6, state_size=32, seed=5)
    before = sub.get_state()
    out = sub.update([1.0, 0.0, -1.0, 0.5, 0.0, 0.2])
    assert not np.array_equal(out, before)
    assert np.array_equal(out, sub.get_state())


def test_deterministic_with_seed():
    a = EchoStateSubstrate(input_size=5, state_size=32, seed=11)
    b = EchoStateSubstrate(input_size=5, state_size=32, seed=11)
    for _ in range(10):
        a.update([0.5, 0.1, 0.9, 0.0, 0.3])
        b.update([0.5, 0.1, 0.9, 0.0, 0.3])
    assert np.array_equal(a.get_state(), b.get_state())


def test_wraps_without_duplicating_the_esn():
    """The wrapper delegates: updating it IS updating the inner ESN."""
    inner = ESN(n_inputs=4, n_reservoir=16, seed=2)
    sub = EchoStateSubstrate.from_esn(inner)
    assert sub.esn is inner
    assert sub.state_size == 16 and sub.input_size == 4
    sub.update([1.0, 0.0, 1.0, 0.0])
    assert np.array_equal(sub.get_state(), np.asarray(inner.state))


def test_matches_raw_esn_numerics():
    """Wrapper output is numerically identical to the unwrapped ESN."""
    raw = ESN(n_inputs=4, n_reservoir=16, seed=7)
    sub = EchoStateSubstrate(input_size=4, state_size=16, seed=7)
    u = [0.3, -0.2, 0.8, 0.1]
    for _ in range(5):
        raw_state = raw.update(u)
        sub_state = sub.update(u)
    assert np.array_equal(np.asarray(raw_state), sub_state)


def test_snapshot_includes_metrics():
    sub = EchoStateSubstrate(input_size=4, state_size=16, seed=1)
    sub.update([1.0, 1.0, 0.0, 0.0])
    snap = sub.snapshot()
    assert snap["name"] == "esn"
    assert "state_norm" in snap["metrics"]
    assert "spectral_radius" in snap["metrics"]["extras"]
    assert snap["metrics"]["spike_rate"] is None  # the ESN does not spike


def test_state_persistence_roundtrip(tmp_path):
    a = EchoStateSubstrate(input_size=4, state_size=16, seed=3)
    for _ in range(8):
        a.update([0.5, 0.5, -0.5, 0.2])
    path = tmp_path / "esn.npz"
    a.save_npz(path)
    b = EchoStateSubstrate(input_size=4, state_size=16, seed=3)
    b.load_npz(path)
    assert np.array_equal(a.get_state(), b.get_state())
