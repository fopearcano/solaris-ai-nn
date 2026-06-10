"""LiquidStateSubstrate -- a small Liquid State Machine *inspired* substrate.

CPU-only, NumPy-only, no spiking library, no gradient training. Each unit keeps
a leaky membrane-like potential; when the potential crosses a threshold (and the
unit is not refractory) the unit emits a spike-like event, the membrane is
soft-reset, and the spike feeds an exponentially fading **liquid trace**. That
analog trace is the substrate's state -- a fading memory of recent spike
activity, which is what the external readout sees.

This is a low-compute *approximation* in the LSM spirit, not a biologically
exact simulation. The readout remains the only trained component.

Update logic per step:

    refractory -= 1 (floored at 0)
    m  = (1 - leak) * m + W_in @ u + W @ trace        leaky integration
    fired = (m >= threshold) & (refractory == 0)      threshold crossing
    m[fired] -= threshold                             soft reset
    refractory[fired] = refractory_period
    trace = trace * trace_decay + fired               fading liquid state
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Sequence, Tuple

import numpy as np

from .base import BaseSubstrate

DEFAULTS: Dict[str, float] = {
    "density": 0.1,           # fraction of non-zero recurrent connections
    "recurrent_gain": 0.9,    # row-normalised recurrent strength
    "input_scaling": 0.5,     # input weight range [-s, +s]
    "leak": 0.3,              # membrane leak rate in (0, 1]
    "threshold": 1.0,         # firing threshold
    "trace_decay": 0.7,       # liquid-trace fading factor in [0, 1)
    "refractory_period": 2,   # steps a unit stays silent after firing
    "membrane_clip": 10.0,    # |membrane| cap (numerical safety)
}


class LiquidStateSubstrate(BaseSubstrate):
    """Leaky membrane + threshold spikes + fading analog liquid trace."""

    name = "liquid_state"

    def __init__(self, input_size: int, state_size: int = 96, seed: int = 0,
                 **params: Any) -> None:
        merged = {**DEFAULTS, **params}
        super().__init__(input_size, state_size, seed, **merged)

    def _build(self) -> None:
        p = self.params
        n, k = self.state_size, self.input_size
        s = float(p["input_scaling"])
        self.W_in = self._rng.uniform(-s, s, size=(n, k))
        mask = self._rng.random((n, n)) < float(p["density"])
        w = self._rng.uniform(-1.0, 1.0, size=(n, n)) * mask
        # Row-sum normalisation keeps recurrent drive bounded without an
        # eigensolver: each unit's total |incoming recurrent weight| <= gain.
        row = np.abs(w).sum(axis=1, keepdims=True)
        row[row == 0.0] = 1.0
        self.W = w * (float(p["recurrent_gain"]) / row)
        self._membrane = np.zeros(n)
        self._trace = np.zeros(n)
        self._refrac = np.zeros(n, dtype=int)
        self._spike_total = 0
        self._last_spikes = 0

    def _update_impl(self, u: np.ndarray) -> np.ndarray:
        p = self.params
        self._refrac = np.maximum(self._refrac - 1, 0)
        inflow = self.W_in @ u + self.W @ self._trace
        self._membrane = (1.0 - float(p["leak"])) * self._membrane + inflow
        clip = float(p["membrane_clip"])
        np.clip(self._membrane, -clip, clip, out=self._membrane)

        fired = (self._membrane >= float(p["threshold"])) & (self._refrac == 0)
        self._membrane = np.where(fired, self._membrane - float(p["threshold"]),
                                  self._membrane)
        self._refrac[fired] = int(p["refractory_period"])
        self._trace = self._trace * float(p["trace_decay"]) + fired.astype(float)

        self._last_spikes = int(fired.sum())
        self._spike_total += self._last_spikes
        return self._trace.copy()

    def _reset_state(self) -> None:
        self._membrane[:] = 0.0
        self._trace[:] = 0.0
        self._refrac[:] = 0
        self._spike_total = 0
        self._last_spikes = 0

    def get_state(self) -> np.ndarray:
        return self._trace.copy()

    def set_state(self, state: Sequence[float]) -> None:
        v = np.asarray(state, dtype=float)
        if v.shape != (self.state_size,):
            raise ValueError("state length mismatch")
        self._trace = v.copy()

    def _arrays(self) -> Dict[str, np.ndarray]:
        return {"state": self._trace.copy(), "membrane": self._membrane.copy(),
                "refractory": self._refrac.copy()}

    def _load_arrays(self, arrays: Dict[str, np.ndarray]) -> None:
        self.set_state(arrays["state"])
        self._membrane = np.asarray(arrays["membrane"], dtype=float).copy()
        self._refrac = np.asarray(arrays["refractory"], dtype=int).copy()

    @property
    def spike_count(self) -> int:
        """Total spikes emitted since the last reset."""
        return self._spike_total

    def _spike_rate(self) -> Optional[float]:
        if self._updates == 0:
            return 0.0
        return self._spike_total / (self._updates * self.state_size)

    def _extra_metrics(self) -> Dict[str, float]:
        return {
            "spike_count": float(self._spike_total),
            "last_spikes": float(self._last_spikes),
            "average_activity": float(np.mean(np.abs(self._trace))),
            "membrane_norm": float(np.linalg.norm(self._membrane)),
        }

    def mutable_parameters(self) -> Dict[str, Tuple[Callable[[], Any], Callable[[Any], None]]]:
        """Plasticity-tunable knobs (bounded by the safety validator)."""
        def setter(key: str, cast=float) -> Callable[[Any], None]:
            def _set(value: Any) -> None:
                self.params[key] = cast(value)
            return _set

        return {
            "threshold": (lambda: float(self.params["threshold"]), setter("threshold")),
            "leak_rate": (lambda: float(self.params["leak"]), setter("leak")),
            "trace_decay": (lambda: float(self.params["trace_decay"]), setter("trace_decay")),
            "refractory_period": (lambda: int(self.params["refractory_period"]),
                                  setter("refractory_period", int)),
        }
