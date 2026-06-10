"""Shared substrate metrics -- simple, documented formulas, nothing exotic.

These are the common numeric lenses applied to any substrate state vector.
Every formula is deliberately elementary; none of them carries a scientific
claim beyond its arithmetic. All functions are safe on zero vectors.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np


def _vec(x: Sequence[float]) -> np.ndarray:
    return np.asarray(x, dtype=float)


def state_norm(state: Sequence[float]) -> float:
    """Euclidean (L2) norm of the state -- coarse activation level."""
    return float(np.linalg.norm(_vec(state)))


def sparsity(state: Sequence[float], eps: float = 1e-6) -> float:
    """Fraction of entries that are (near-)zero. 1.0 = fully silent vector."""
    v = _vec(state)
    if v.size == 0:
        return 0.0
    return float(np.mean(np.abs(v) <= eps))


def activity_rate(state: Sequence[float], threshold: float = 0.05) -> float:
    """Fraction of units whose |value| exceeds ``threshold`` ("active" units)."""
    v = _vec(state)
    if v.size == 0:
        return 0.0
    return float(np.mean(np.abs(v) > threshold))


def state_drift(a: Sequence[float], b: Sequence[float]) -> float:
    """Euclidean distance between two states -- how much the substrate moved."""
    va, vb = _vec(a), _vec(b)
    if va.shape != vb.shape:
        raise ValueError(f"state shape mismatch: {va.shape} vs {vb.shape}")
    return float(np.linalg.norm(va - vb))


def activity_entropy(state: Sequence[float]) -> float:
    """Normalised entropy of the |state| distribution in [0, 1].

    0 = all activity in one unit; 1 = perfectly even activity. A zero vector
    has no distribution and returns 0.0. This is an *evenness* estimate, not an
    information-theoretic claim about the substrate.
    """
    v = np.abs(_vec(state))
    total = float(v.sum())
    if v.size <= 1 or total <= 0.0:
        return 0.0
    p = v / total
    p = p[p > 0]
    h = float(-(p * np.log(p)).sum())
    return h / math.log(v.size)


def saturation_ratio(state: Sequence[float], limit: float = 0.95) -> float:
    """Fraction of units at/above ``limit`` in magnitude (pinned units)."""
    v = _vec(state)
    if v.size == 0:
        return 0.0
    return float(np.mean(np.abs(v) >= limit))


def silence_ratio(state: Sequence[float], eps: float = 1e-3) -> float:
    """Fraction of units with |value| <= eps (effectively silent units)."""
    v = _vec(state)
    if v.size == 0:
        return 0.0
    return float(np.mean(np.abs(v) <= eps))


def trace_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity between two state vectors (0.0 if either is zero)."""
    va, vb = _vec(a), _vec(b)
    na, nb = float(np.linalg.norm(va)), float(np.linalg.norm(vb))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))
