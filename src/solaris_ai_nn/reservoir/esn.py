"""Echo State Network (ESN) reservoir -- a low-compute temporal substrate.

This is **not** a powerful model. It is a small, fixed, randomly-initialised
recurrent network whose internal state is a fading echo of the input history.
Only a linear readout (see :mod:`solaris_ai_nn.reservoir.readout`) is trained,
so there is no backpropagation through time and almost no compute cost per step.

Why a reservoir for Solaris-AI-NN?

* It gives the system a *continuous nervous substrate* whose state depends on the
  whole event history, which matches the "continuous cognition" goal.
* Adaptation is cheap and online: train one linear layer, not the recurrence.
* It is fully transparent -- every matrix can be printed and inspected.

Design (pure stdlib, CPU-only, deterministic given a seed):

* sparse recurrent matrix ``W`` (most entries zero)
* spectral-radius normalisation toward the Echo State Property
* dense input projection ``W_in``
* leaky-integrator tanh state update
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from ..utils.math import (
    Matrix,
    Vector,
    mat_vec,
    scale_matrix,
    spectral_radius_estimate,
    tanh_vec,
    zeros,
)


@dataclass
class ESN:
    """A leaky-integrator Echo State Network reservoir.

    Args:
        n_inputs: Dimensionality of the input feature vector.
        n_reservoir: Number of reservoir units (default 64; keep small).
        spectral_radius: Target |largest eigenvalue| of ``W`` (< 1 for the Echo
            State Property; 0.9 is a safe default).
        leak_rate: Leaky-integration rate in (0, 1]. Lower = slower, longer
            memory; 1.0 = no leak.
        input_scaling: Multiplier applied to input weights.
        sparsity: Fraction of recurrent connections that are non-zero.
        seed: RNG seed for fully deterministic initialisation.
    """

    n_inputs: int
    n_reservoir: int = 64
    spectral_radius: float = 0.9
    leak_rate: float = 0.3
    input_scaling: float = 1.0
    sparsity: float = 0.1
    seed: int = 0

    # Internal weights / state (built in __post_init__).
    W_in: Matrix = field(default_factory=list, repr=False)
    W: Matrix = field(default_factory=list, repr=False)
    _state: Vector = field(default_factory=list, repr=False)
    _achieved_radius: float = 0.0

    def __post_init__(self) -> None:
        if not (0.0 < self.leak_rate <= 1.0):
            raise ValueError("leak_rate must be in (0, 1]")
        if not (0.0 < self.sparsity <= 1.0):
            raise ValueError("sparsity must be in (0, 1]")
        rng = random.Random(self.seed)
        self.W_in = self._build_input_weights(rng)
        self.W = self._build_recurrent_weights(rng)
        self._state = zeros(self.n_reservoir)

    # -- construction -------------------------------------------------------

    def _build_input_weights(self, rng: random.Random) -> Matrix:
        """Dense input projection in [-input_scaling, +input_scaling]."""
        s = self.input_scaling
        return [
            [rng.uniform(-s, s) for _ in range(self.n_inputs)]
            for _ in range(self.n_reservoir)
        ]

    def _build_recurrent_weights(self, rng: random.Random) -> Matrix:
        """Sparse recurrent matrix, rescaled to the target spectral radius."""
        n = self.n_reservoir
        w: Matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if rng.random() < self.sparsity:
                    w[i][j] = rng.uniform(-1.0, 1.0)

        radius = spectral_radius_estimate(w, seed=self.seed)
        if radius > 0.0:
            w = scale_matrix(w, self.spectral_radius / radius)
            self._achieved_radius = self.spectral_radius
        else:
            # Degenerate (all-zero) matrix: leave as-is, radius stays 0.
            self._achieved_radius = 0.0
        return w

    # -- dynamics -----------------------------------------------------------

    def update(self, input_vec: Vector) -> Vector:
        """Advance the reservoir one step and return the new state.

        Leaky-integrator update::

            pre = W_in @ u + W @ x
            x' = (1 - leak) * x + leak * tanh(pre)

        Args:
            input_vec: Feature vector of length ``n_inputs``.

        Returns:
            The updated reservoir state (a copy is held internally).
        """
        if len(input_vec) != self.n_inputs:
            raise ValueError(
                f"expected input of length {self.n_inputs}, got {len(input_vec)}"
            )
        pre_in = mat_vec(self.W_in, input_vec)
        pre_rec = mat_vec(self.W, self._state)
        activated = tanh_vec([a + b for a, b in zip(pre_in, pre_rec)])
        leak = self.leak_rate
        self._state = [
            (1.0 - leak) * x + leak * a for x, a in zip(self._state, activated)
        ]
        return list(self._state)

    def reset(self, state: Optional[Vector] = None) -> None:
        """Reset the reservoir state to zeros (or to a provided state)."""
        if state is None:
            self._state = zeros(self.n_reservoir)
        else:
            if len(state) != self.n_reservoir:
                raise ValueError("state length mismatch")
            self._state = list(state)

    # -- inspection ---------------------------------------------------------

    @property
    def state(self) -> Vector:
        """Current reservoir state (a defensive copy)."""
        return list(self._state)

    @property
    def achieved_spectral_radius(self) -> float:
        """The spectral radius the recurrent matrix was rescaled to."""
        return self._achieved_radius

    def feature_size(self) -> int:
        """Length of the feature vector a readout sees (state + bias term)."""
        return self.n_reservoir + 1

    def features(self) -> List[float]:
        """Reservoir state augmented with a constant bias feature (1.0)."""
        return self.state + [1.0]

    # -- controlled, recomputable parameter setters (used by plasticity) ----

    def set_leak_rate(self, value: float) -> None:
        """Set the leaky-integration rate (takes effect on the next update)."""
        if not (0.0 < value <= 1.0):
            raise ValueError("leak_rate must be in (0, 1]")
        self.leak_rate = value

    def set_input_scaling(self, value: float) -> None:
        """Rescale the input weights so ``input_scaling`` becomes ``value``.

        Rescales ``W_in`` by ``value / current`` so the change is immediate and
        reversible (setting the old value back restores the original weights).
        """
        if value <= 0.0:
            raise ValueError("input_scaling must be > 0")
        current = self.input_scaling
        if current == 0.0:
            return
        factor = value / current
        self.W_in = [[w * factor for w in row] for row in self.W_in]
        self.input_scaling = value

    def set_spectral_radius(self, value: float) -> None:
        """Rescale the recurrent matrix to a new spectral radius.

        Scales ``W`` by ``value / achieved`` -- cheap and reversible, no eigen
        recompute needed. Bounds are enforced by the plasticity safety validator.
        """
        if value <= 0.0:
            raise ValueError("spectral_radius must be > 0")
        achieved = self._achieved_radius
        if achieved <= 0.0:
            return
        factor = value / achieved
        self.W = [[w * factor for w in row] for row in self.W]
        self._achieved_radius = value
        self.spectral_radius = value

