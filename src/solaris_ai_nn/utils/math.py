"""Tiny pure-stdlib linear-algebra helpers.

Solaris-AI-NN deliberately avoids NumPy in its first version (see README and
``docs/RESEARCH_NOTES.md``). The reservoir is small (64-128 units) and the goal
is *transparency*, not raw throughput, so a handful of explicit list-based
operations are clearer than a hidden BLAS call and keep the package
dependency-free. A NumPy-backed accelerator is a Phase-4 option, not a
requirement.

Everything here operates on plain Python lists:

* ``Vector`` is ``list[float]``
* ``Matrix`` is ``list[list[float]]`` (row-major)
"""

from __future__ import annotations

import math
from typing import List, Sequence

Vector = List[float]
Matrix = List[List[float]]


def zeros(n: int) -> Vector:
    """Return a zero vector of length ``n``."""
    return [0.0] * n


def zeros_matrix(rows: int, cols: int) -> Matrix:
    """Return a ``rows`` x ``cols`` zero matrix."""
    return [[0.0] * cols for _ in range(rows)]


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    """Inner product of two equal-length sequences."""
    if len(a) != len(b):
        raise ValueError(f"length mismatch: {len(a)} != {len(b)}")
    return math.fsum(x * y for x, y in zip(a, b))


def mat_vec(matrix: Matrix, vec: Sequence[float]) -> Vector:
    """Matrix-vector product ``matrix @ vec``."""
    return [dot(row, vec) for row in matrix]


def vec_add(a: Sequence[float], b: Sequence[float]) -> Vector:
    """Element-wise sum."""
    return [x + y for x, y in zip(a, b)]


def vec_sub(a: Sequence[float], b: Sequence[float]) -> Vector:
    """Element-wise difference ``a - b``."""
    return [x - y for x, y in zip(a, b)]


def vec_scale(vec: Sequence[float], factor: float) -> Vector:
    """Scale every element by ``factor``."""
    return [x * factor for x in vec]


def tanh_vec(vec: Sequence[float]) -> Vector:
    """Element-wise hyperbolic tangent (the reservoir non-linearity)."""
    return [math.tanh(x) for x in vec]


def norm(vec: Sequence[float]) -> float:
    """Euclidean (L2) norm."""
    return math.sqrt(math.fsum(x * x for x in vec))


def clamp(value: float, low: float, high: float) -> float:
    """Clamp ``value`` into the inclusive range ``[low, high]``."""
    return max(low, min(high, value))


def scale_matrix(matrix: Matrix, factor: float) -> Matrix:
    """Return a new matrix with every entry multiplied by ``factor``."""
    return [[v * factor for v in row] for row in matrix]


def spectral_radius_estimate(matrix: Matrix, iters: int = 100, seed: int = 0) -> float:
    """Estimate the spectral radius (largest |eigenvalue|) via power iteration.

    Power iteration converges to the magnitude of the dominant eigenvalue
    without needing NumPy/eig. It is exact enough for normalising a reservoir's
    recurrent matrix; the reservoir is then rescaled so its spectral radius
    matches the desired Echo State Property target.

    Args:
        matrix: Square matrix.
        iters: Number of power-iteration steps.
        seed: Seed for the random starting vector (determinism).

    Returns:
        Estimated spectral radius (``0.0`` for an empty / all-zero matrix).
    """
    import random as _random

    n = len(matrix)
    if n == 0:
        return 0.0

    rng = _random.Random(seed)
    v = [rng.uniform(-1.0, 1.0) for _ in range(n)]
    nv = norm(v)
    if nv == 0.0:
        return 0.0
    v = vec_scale(v, 1.0 / nv)

    eigval = 0.0
    for _ in range(iters):
        w = mat_vec(matrix, v)
        nw = norm(w)
        if nw == 0.0:
            return 0.0
        eigval = nw  # ||M v|| with v unit-norm approximates |lambda_max|
        v = vec_scale(w, 1.0 / nw)
    return eigval
