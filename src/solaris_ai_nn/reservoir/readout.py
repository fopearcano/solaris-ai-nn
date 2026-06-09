"""Linear readout layer -- the only trainable part of the substrate.

The readout maps reservoir features to one score per candidate action. In
Solaris-AI-NN the score is interpreted as an *expected reaction valence* for
taking that action in the current context: the loop picks the action with the
highest score (plus a light habit bias). Training nudges the score toward the
valence actually observed (see :mod:`solaris_ai_nn.reservoir.online_learning`).

Keeping this linear is deliberate: it is cheap, interpretable, and trainable
online without any deep-learning framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..utils.math import Vector, dot, zeros_matrix

Matrix = List[List[float]]


@dataclass
class LinearReadout:
    """A simple ``n_outputs x n_features`` linear map.

    The bias is folded into the features (the ESN appends a constant 1.0), so
    there is no separate bias vector here -- one less moving part.

    Args:
        n_features: Length of the input feature vector (reservoir state + bias).
        n_outputs: Number of action scores to produce.
        labels: Optional human-readable label per output index.
    """

    n_features: int
    n_outputs: int
    labels: List[str] = field(default_factory=list)
    weights: Matrix = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        if not self.weights:
            self.weights = zeros_matrix(self.n_outputs, self.n_features)
        if not self.labels:
            self.labels = [f"action_{i}" for i in range(self.n_outputs)]
        if len(self.labels) != self.n_outputs:
            raise ValueError("labels length must equal n_outputs")

    def predict(self, features: Vector) -> Vector:
        """Return one score per output (``weights @ features``)."""
        if len(features) != self.n_features:
            raise ValueError(
                f"expected {self.n_features} features, got {len(features)}"
            )
        return [dot(row, features) for row in self.weights]

    def argmax(self, features: Vector, bias: Vector | None = None) -> int:
        """Index of the highest score, optionally offset by a per-action bias."""
        scores = self.predict(features)
        if bias is not None:
            scores = [s + b for s, b in zip(scores, bias)]
        best = 0
        best_val = scores[0]
        for i, v in enumerate(scores):
            if v > best_val:
                best_val = v
                best = i
        return best

    def weight_magnitude(self) -> float:
        """Sum of |weight| over the whole matrix (a coarse capacity metric)."""
        return sum(abs(w) for row in self.weights for w in row)

    def nonzero_count(self) -> int:
        """Number of non-zero weights (drops as synthesis prunes)."""
        return sum(1 for row in self.weights for w in row if w != 0.0)
