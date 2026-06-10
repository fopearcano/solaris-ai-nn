"""Common interface for all low-compute neural substrates.

Solaris-AI-NN is a substrate *laboratory*: different continuous, event-driven,
low-compute "nervous substrates" (ESN, liquid-state, spiking-recurrent) must be
interchangeable under the same Solaris signal ecology. This module defines the
contract they all satisfy:

    update(input_vector) -> np.ndarray     advance one step, return new state
    reset()                                 zero the evolving state
    get_state() / set_state(state)          read / write the primary state vector
    snapshot() -> dict                      JSON-friendly self-description
    save_npz(path) / load_npz(path)         full-fidelity binary persistence
    metrics() -> SubstrateMetrics           shared numeric health metrics

None of the substrates train their recurrent core; the linear readout remains
the only adaptive layer (see ``reservoir/readout.py``). NumPy enters the
project here -- the substrate lab is the place dense vector math earns it.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Union

import numpy as np

from . import metrics as M


@dataclass
class SubstrateConfig:
    """Serializable description of how a substrate was built."""

    name: str
    input_size: int
    state_size: int
    seed: int
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubstrateConfig":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class SubstrateState:
    """A point-in-time carrier of a substrate's evolving state."""

    vector: list
    updates: int = 0
    extras: Dict[str, list] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"vector": list(self.vector), "updates": self.updates,
                "extras": {k: list(v) for k, v in self.extras.items()}}


@dataclass
class SubstrateMetrics:
    """Shared numeric health metrics every substrate reports."""

    state_norm: float = 0.0
    sparsity: float = 0.0
    activity_rate: float = 0.0
    drift: float = 0.0
    entropy: float = 0.0
    saturation_ratio: float = 0.0
    silence_ratio: float = 0.0
    spike_rate: Optional[float] = None
    updates: int = 0
    extras: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseSubstrate:
    """Base class for all substrates; subclasses implement ``_update_impl``.

    Args:
        input_size: Length of the encoded event vectors fed in.
        state_size: Number of substrate units.
        seed: Determinism seed (drives all random initialisation).
        **params: Substrate-specific parameters (recorded in the config).
    """

    name: str = "base"

    def __init__(self, input_size: int, state_size: int = 64, seed: int = 0,
                 **params: Any) -> None:
        if input_size <= 0 or state_size <= 0:
            raise ValueError("input_size and state_size must be positive")
        self.input_size = int(input_size)
        self.state_size = int(state_size)
        self.seed = int(seed)
        self.params: Dict[str, Any] = dict(params)
        self._rng = np.random.default_rng(self.seed)
        self._updates = 0
        self._last_drift = 0.0
        self._build()

    # -- subclass hooks -------------------------------------------------------

    def _build(self) -> None:
        """Build weights and initial state. Subclasses override."""
        raise NotImplementedError

    def _update_impl(self, u: np.ndarray) -> np.ndarray:
        """Advance one step and return the new primary state."""
        raise NotImplementedError

    def _arrays(self) -> Dict[str, np.ndarray]:
        """All evolving arrays needed for full-fidelity save/load."""
        return {"state": self.get_state()}

    def _load_arrays(self, arrays: Dict[str, np.ndarray]) -> None:
        """Restore evolving arrays produced by :meth:`_arrays`."""
        self.set_state(arrays["state"])

    def _extra_metrics(self) -> Dict[str, float]:
        """Substrate-specific metric extras (override as useful)."""
        return {}

    def _spike_rate(self) -> Optional[float]:
        """Recent spike rate, if the substrate spikes (else ``None``)."""
        return None

    # -- common API -----------------------------------------------------------

    def update(self, input_vector: Sequence[float]) -> np.ndarray:
        """Advance the substrate one step; returns the new state vector."""
        u = np.asarray(input_vector, dtype=float)
        if u.shape != (self.input_size,):
            raise ValueError(
                f"expected input of length {self.input_size}, got {u.shape}")
        prev = self.get_state()
        out = self._update_impl(u)
        self._updates += 1
        self._last_drift = M.state_drift(out, prev)
        return out

    def reset(self) -> None:
        """Zero the evolving state (weights are untouched)."""
        self._reset_state()
        self._updates = 0
        self._last_drift = 0.0

    def _reset_state(self) -> None:
        raise NotImplementedError

    def get_state(self) -> np.ndarray:
        """Copy of the primary state vector."""
        raise NotImplementedError

    def set_state(self, state: Sequence[float]) -> None:
        """Overwrite the primary state vector (length must match)."""
        raise NotImplementedError

    @property
    def config(self) -> SubstrateConfig:
        return SubstrateConfig(
            name=self.name, input_size=self.input_size,
            state_size=self.state_size, seed=self.seed, params=dict(self.params))

    def metrics(self) -> SubstrateMetrics:
        s = self.get_state()
        return SubstrateMetrics(
            state_norm=M.state_norm(s),
            sparsity=M.sparsity(s),
            activity_rate=M.activity_rate(s),
            drift=self._last_drift,
            entropy=M.activity_entropy(s),
            saturation_ratio=M.saturation_ratio(s),
            silence_ratio=M.silence_ratio(s),
            spike_rate=self._spike_rate(),
            updates=self._updates,
            extras=self._extra_metrics(),
        )

    def mutable_parameters(self) -> Dict[str, Tuple[Callable[[], Any], Callable[[Any], None]]]:
        """``param -> (getter, setter)`` for plasticity-tunable knobs (default none)."""
        return {}

    def snapshot(self) -> Dict[str, Any]:
        """JSON-friendly description of the substrate right now."""
        state = self.get_state()
        return {
            "name": self.name,
            "config": self.config.to_dict(),
            "updates": self._updates,
            "state_sample": [float(x) for x in state[:5]],
            "metrics": self.metrics().to_dict(),
        }

    # -- persistence ----------------------------------------------------------

    def save_npz(self, path: Union[str, Path]) -> None:
        """Save full evolving state + config to a ``.npz`` file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        meta = json.dumps({"config": self.config.to_dict(), "updates": self._updates})
        np.savez(path, __meta__=np.array(meta), **self._arrays())

    def load_npz(self, path: Union[str, Path]) -> None:
        """Restore evolving state from :meth:`save_npz` output.

        The substrate must already be constructed with a matching config (the
        registry/persistence layer verifies this via the manifest).
        """
        with np.load(Path(path), allow_pickle=False) as data:
            meta = json.loads(str(data["__meta__"]))
            arrays = {k: data[k] for k in data.files if k != "__meta__"}
        saved = meta.get("config", {})
        if saved.get("state_size") not in (None, self.state_size) or \
           saved.get("input_size") not in (None, self.input_size):
            raise ValueError("saved substrate shape does not match this substrate")
        self._load_arrays(arrays)
        self._updates = int(meta.get("updates", 0))
