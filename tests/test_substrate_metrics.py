"""Tests for the shared substrate metric functions."""

from __future__ import annotations

import math

import numpy as np
import pytest

from solaris_ai_nn.substrates import metrics as M


def test_state_norm():
    assert M.state_norm([3.0, 4.0]) == 5.0
    assert M.state_norm([0.0, 0.0]) == 0.0


def test_sparsity():
    assert M.sparsity([0.0, 0.0, 1.0, 0.5]) == 0.5
    assert M.sparsity([0.0, 0.0]) == 1.0  # all zero => fully sparse
    assert M.sparsity([]) == 0.0          # empty handled safely


def test_activity_rate():
    assert M.activity_rate([0.0, 0.01, 0.5, 1.0], threshold=0.05) == 0.5
    assert M.activity_rate(np.zeros(8)) == 0.0


def test_drift():
    assert M.state_drift([1.0, 0.0], [0.0, 0.0]) == 1.0
    assert M.state_drift([1.0, 1.0], [1.0, 1.0]) == 0.0
    with pytest.raises(ValueError):
        M.state_drift([1.0], [1.0, 2.0])


def test_entropy_bounds_and_zero_vector():
    # Zero vector: no distribution -> 0.0, no crash.
    assert M.activity_entropy(np.zeros(10)) == 0.0
    # All activity in one unit -> 0 (fully concentrated).
    assert M.activity_entropy([0.0, 0.0, 5.0]) == 0.0
    # Perfectly even -> 1.0 (normalised maximum).
    even = M.activity_entropy([1.0, 1.0, 1.0, 1.0])
    assert math.isclose(even, 1.0, rel_tol=1e-9)
    # Anything else lands strictly in between.
    mid = M.activity_entropy([1.0, 0.5, 0.1])
    assert 0.0 < mid < 1.0


def test_saturation_and_silence_ratios():
    v = [0.0, 0.96, 1.0, 0.3]
    assert M.saturation_ratio(v, limit=0.95) == 0.5
    assert M.silence_ratio(v, eps=1e-3) == 0.25
    assert M.saturation_ratio(np.zeros(4)) == 0.0
    assert M.silence_ratio(np.zeros(4)) == 1.0


def test_trace_similarity_zero_safe():
    assert M.trace_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert M.trace_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert M.trace_similarity([1.0, 0.0], [0.0, 0.0]) == 0.0  # zero vector safe
    assert math.isclose(M.trace_similarity([1.0, 0.0], [-1.0, 0.0]), -1.0)
