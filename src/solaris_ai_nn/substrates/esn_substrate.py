"""EchoStateSubstrate -- the existing list-based ESN, wrapped as a substrate.

The Prompt-1 Echo State Network (``reservoir/esn.py``) stays exactly as it is;
this adapter makes it one selectable substrate among several. No ESN logic is
duplicated -- ``update`` delegates to the wrapped ``ESN`` so the numerical path
(and therefore every existing deterministic result) is unchanged.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Sequence, Tuple

import numpy as np

from ..reservoir.esn import ESN
from .base import BaseSubstrate

# ESN constructor kwargs the wrapper forwards.
_ESN_PARAMS = ("spectral_radius", "leak_rate", "input_scaling", "sparsity")


class EchoStateSubstrate(BaseSubstrate):
    """Adapter exposing the list-based :class:`ESN` through the substrate API."""

    name = "esn"

    def __init__(self, input_size: int, state_size: int = 64, seed: int = 0,
                 esn: Optional[ESN] = None, **params: Any) -> None:
        self._wrapped = esn  # consumed by _build
        super().__init__(input_size, state_size, seed, **params)

    @classmethod
    def from_esn(cls, esn: ESN) -> "EchoStateSubstrate":
        """Wrap an already-constructed ESN (legacy bridge path)."""
        return cls(input_size=esn.n_inputs, state_size=esn.n_reservoir,
                   seed=esn.seed, esn=esn)

    def _build(self) -> None:
        if self._wrapped is not None:
            self.esn = self._wrapped
            self.input_size = self.esn.n_inputs
            self.state_size = self.esn.n_reservoir
            self.seed = self.esn.seed
        else:
            kwargs = {k: v for k, v in self.params.items() if k in _ESN_PARAMS}
            self.esn = ESN(n_inputs=self.input_size, n_reservoir=self.state_size,
                           seed=self.seed, **kwargs)

    def _update_impl(self, u: np.ndarray) -> np.ndarray:
        return np.asarray(self.esn.update([float(x) for x in u]), dtype=float)

    def _reset_state(self) -> None:
        self.esn.reset()

    def get_state(self) -> np.ndarray:
        return np.asarray(self.esn.state, dtype=float)

    def set_state(self, state: Sequence[float]) -> None:
        self.esn.reset([float(x) for x in state])

    def _extra_metrics(self) -> Dict[str, float]:
        n = self.esn.n_reservoir
        nonzero = sum(1 for row in self.esn.W for w in row if w != 0.0)
        return {
            "spectral_radius": float(self.esn.achieved_spectral_radius),
            "connection_density": nonzero / (n * n) if n else 0.0,
            "leak_rate": float(self.esn.leak_rate),
        }

    def mutable_parameters(self) -> Dict[str, Tuple[Callable[[], Any], Callable[[Any], None]]]:
        # ESN knobs are already registered under the "reservoir" plasticity
        # component (via bridge.esn); nothing extra here to avoid duplicates.
        return {}
