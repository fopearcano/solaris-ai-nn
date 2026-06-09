"""Online readout learning -- weak, continuous adaptation.

Implements a reward-modulated *normalized* delta rule (NLMS / normalized
Widrow-Hoff). After every event the loop knows: which action was taken, the
feature vector that produced it, and the reaction valence that followed. We
update only the row of the chosen action, nudging its predicted value toward the
observed valence::

    error = valence - score[chosen]
    step  = lr * error / (eps + ||features||^2)
    W[chosen] += step * features

The normalisation by ``||features||^2`` is what makes this stable on a
reservoir's many correlated, similarly-scaled features: a plain LMS step
(``lr * error * features``) diverges because the effective step grows with the
feature dimension. NLMS keeps the update well-conditioned for any ``lr`` in
roughly ``(0, 2)``, independent of reservoir size.

This embodies the core Solaris bet that the project is built to test:

    long-running weak adaptation  >  expensive one-shot intelligence

No deep-learning framework, no batch, no replay buffer -- one cheap update per
event. (A recursive-least-squares variant is a documented Phase-4 option.)
"""

from __future__ import annotations

from dataclasses import dataclass

from .readout import LinearReadout
from ..utils.math import Vector, clamp


@dataclass
class DeltaRuleLearner:
    """Reward-modulated normalized delta-rule trainer for a :class:`LinearReadout`.

    Args:
        lr: Learning rate / step size in ~(0, 2). Smaller => slower, steadier.
        weight_clip: Absolute cap on any single weight, keeping the linear map
            bounded during long runs (plasticity without runaway growth).
        eps: Small constant guarding the norm normalisation against zero input.
    """

    lr: float = 0.3
    weight_clip: float = 10.0
    eps: float = 1e-6

    def update(
        self,
        readout: LinearReadout,
        features: Vector,
        chosen: int,
        valence: float,
    ) -> float:
        """Apply one online (NLMS) update for the chosen action.

        Args:
            readout: The readout whose weights are updated in place.
            features: Feature vector that produced the action.
            chosen: Index of the action that was taken.
            valence: Observed reaction valence in [-1, +1] (the target).

        Returns:
            The signed prediction error ``valence - predicted_score``.
        """
        scores = readout.predict(features)
        error = valence - scores[chosen]
        norm_sq = sum(x * x for x in features)
        step = self.lr * error / (self.eps + norm_sq)
        row = readout.weights[chosen]
        clip = self.weight_clip
        for j, x in enumerate(features):
            row[j] = clamp(row[j] + step * x, -clip, clip)
        return error
