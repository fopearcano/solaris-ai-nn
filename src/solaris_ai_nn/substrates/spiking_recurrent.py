"""SpikingRecurrentSubstrate -- sparse **binary** spike events as state.

A simple leaky integrate-and-fire *inspired* recurrent substrate. Unlike
:class:`LiquidStateSubstrate` (whose state is an analog fading trace), this
substrate's primary state is the **instantaneous binary spike vector**: which
units fired this step. That makes its events maximally sparse and discrete --
the other end of the low-compute substrate spectrum.

Per step:

    refractory -= 1 (floored at 0)
    v = decay * v + W_in @ u + W @ spikes_prev (+ optional seeded noise)
    fired = (v >= threshold) & (refractory == 0)
    v[fired] = 0                      hard reset
    refractory[fired] = refractory_period
    spikes = fired (binary 0/1)       <- the substrate state

No training inside the recurrent core; the external readout adapts. With zero
input and no noise, membranes decay geometrically -- activity is bounded and
fades, it cannot blow up.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Sequence, Tuple

import numpy as np

from .base import BaseSubstrate

DEFAULTS: Dict[str, float] = {
    "density": 0.15,          # fraction of non-zero recurrent connections
    "recurrent_gain": 1.2,    # row-normalised recurrent strength
    "input_scaling": 0.8,     # input weight range [-s, +s]
    "decay": 0.9,             # membrane decay factor in [0, 1)
    "threshold": 1.0,         # firing threshold
    "refractory_period": 3,   # steps a unit stays silent after firing
    "noise_level": 0.0,       # optional uniform membrane noise amplitude
    "membrane_clip": 10.0,    # |membrane| cap (numerical safety)
    "rate_ema": 0.95,         # smoothing for the per-unit spike-rate estimate
}


class SpikingRecurrentSubstrate(BaseSubstrate):
    """Binary spikes over a sparse recurrent matrix with refractory periods."""

    name = "spiking_recurrent"

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
        row = np.abs(w).sum(axis=1, keepdims=True)
        row[row == 0.0] = 1.0
        self.W = w * (float(p["recurrent_gain"]) / row)
        self._v = np.zeros(n)
        self._spikes = np.zeros(n)
        self._refrac = np.zeros(n, dtype=int)
        self._unit_rate = np.zeros(n)  # per-unit EMA spike rate

    def _update_impl(self, u: np.ndarray) -> np.ndarray:
        p = self.params
        self._refrac = np.maximum(self._refrac - 1, 0)
        v = float(p["decay"]) * self._v + self.W_in @ u + self.W @ self._spikes
        noise = float(p["noise_level"])
        if noise > 0.0:
            v = v + self._rng.uniform(-noise, noise, size=self.state_size)
        clip = float(p["membrane_clip"])
        v = np.clip(v, -clip, clip)

        fired = (v >= float(p["threshold"])) & (self._refrac == 0)
        self._v = np.where(fired, 0.0, v)
        self._refrac[fired] = int(p["refractory_period"])
        self._spikes = fired.astype(float)

        ema = float(p["rate_ema"])
        self._unit_rate = ema * self._unit_rate + (1.0 - ema) * self._spikes
        return self._spikes.copy()

    def _reset_state(self) -> None:
        self._v[:] = 0.0
        self._spikes[:] = 0.0
        self._refrac[:] = 0
        self._unit_rate[:] = 0.0

    def get_state(self) -> np.ndarray:
        return self._spikes.copy()

    def set_state(self, state: Sequence[float]) -> None:
        v = np.asarray(state, dtype=float)
        if v.shape != (self.state_size,):
            raise ValueError("state length mismatch")
        self._spikes = (v > 0.5).astype(float)  # re-binarise defensively

    def _arrays(self) -> Dict[str, np.ndarray]:
        return {"state": self._spikes.copy(), "membrane": self._v.copy(),
                "refractory": self._refrac.copy(), "unit_rate": self._unit_rate.copy()}

    def _load_arrays(self, arrays: Dict[str, np.ndarray]) -> None:
        self.set_state(arrays["state"])
        self._v = np.asarray(arrays["membrane"], dtype=float).copy()
        self._refrac = np.asarray(arrays["refractory"], dtype=int).copy()
        self._unit_rate = np.asarray(arrays["unit_rate"], dtype=float).copy()

    # -- metrics --------------------------------------------------------------

    def _spike_rate(self) -> Optional[float]:
        return float(np.mean(self._unit_rate))

    def _extra_metrics(self) -> Dict[str, float]:
        return {
            "silent_units_ratio": float(np.mean(self._unit_rate < 0.01)),
            "saturated_units_ratio": float(np.mean(self._unit_rate > 0.9)),
            "recurrent_activity_norm": float(np.linalg.norm(self.W @ self._spikes)),
            "membrane_norm": float(np.linalg.norm(self._v)),
            "last_spike_count": float(self._spikes.sum()),
        }

    def mutable_parameters(self) -> Dict[str, Tuple[Callable[[], Any], Callable[[Any], None]]]:
        """Plasticity-tunable knobs (bounded by the safety validator)."""
        def setter(key: str, cast=float) -> Callable[[Any], None]:
            def _set(value: Any) -> None:
                self.params[key] = cast(value)
            return _set

        return {
            "threshold": (lambda: float(self.params["threshold"]), setter("threshold")),
            "decay": (lambda: float(self.params["decay"]), setter("decay")),
            "noise_level": (lambda: float(self.params["noise_level"]), setter("noise_level")),
            "refractory_period": (lambda: int(self.params["refractory_period"]),
                                  setter("refractory_period", int)),
        }
