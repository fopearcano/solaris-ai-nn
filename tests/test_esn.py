"""Tests for the Echo State Network reservoir."""

from __future__ import annotations

import math

from solaris_ai_nn.reservoir.esn import ESN
from solaris_ai_nn.utils.math import spectral_radius_estimate


def _zero_input(esn: ESN):
    return [0.0] * esn.n_inputs


def test_default_size_and_state_shape():
    esn = ESN(n_inputs=10)
    assert esn.n_reservoir == 64
    assert len(esn.state) == 64
    assert esn.feature_size() == 65  # state + bias
    assert len(esn.features()) == 65
    assert esn.features()[-1] == 1.0


def test_deterministic_with_same_seed():
    a = ESN(n_inputs=8, n_reservoir=32, seed=123)
    b = ESN(n_inputs=8, n_reservoir=32, seed=123)
    u = [0.1 * i for i in range(8)]
    sa = a.update(u)
    sb = b.update(u)
    assert sa == sb


def test_different_seed_differs():
    a = ESN(n_inputs=8, n_reservoir=32, seed=1)
    b = ESN(n_inputs=8, n_reservoir=32, seed=2)
    u = [0.1 * i for i in range(8)]
    assert a.update(u) != b.update(u)


def test_state_changes_on_update():
    esn = ESN(n_inputs=6, n_reservoir=32, seed=5)
    before = esn.state
    after = esn.update([1.0, 0.0, -1.0, 0.5, 0.0, 0.2])
    assert before != after
    assert any(abs(x) > 0 for x in after)


def test_reset_clears_state():
    esn = ESN(n_inputs=6, n_reservoir=32, seed=5)
    esn.update([1.0] * 6)
    assert any(abs(x) > 0 for x in esn.state)
    esn.reset()
    assert all(x == 0.0 for x in esn.state)


def test_spectral_radius_normalised():
    esn = ESN(n_inputs=4, n_reservoir=64, spectral_radius=0.9, seed=42)
    est = spectral_radius_estimate(esn.W, iters=200, seed=1)
    # Power-iteration estimate should land close to the configured target.
    assert math.isclose(est, 0.9, rel_tol=0.15)


def test_state_stays_bounded_under_constant_drive():
    # Echo State Property: bounded state for bounded input.
    esn = ESN(n_inputs=4, n_reservoir=64, spectral_radius=0.9, seed=7)
    for _ in range(500):
        esn.update([1.0, -1.0, 0.5, -0.5])
    assert all(abs(x) <= 1.0 + 1e-6 for x in esn.state)
