"""SubstrateRegistry -- create substrates by name, with validated configs.

The registry is the single catalogue of available low-compute substrates. The
bridge, the switcher, and the experiments all go through it, so a new substrate
only needs to be registered here to become selectable everywhere.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from .base import BaseSubstrate, SubstrateConfig
from .esn_substrate import EchoStateSubstrate
from .liquid_state import LiquidStateSubstrate
from .spiking_recurrent import SpikingRecurrentSubstrate

# Default state sizes per substrate (kept small: low-compute by design).
_DEFAULT_STATE_SIZE: Dict[str, int] = {
    "esn": 64,
    "liquid_state": 96,
    "spiking_recurrent": 96,
}


class SubstrateRegistry:
    """Catalogue of substrate classes, keyed by name."""

    _classes: Dict[str, Type[BaseSubstrate]] = {
        "esn": EchoStateSubstrate,
        "liquid_state": LiquidStateSubstrate,
        "spiking_recurrent": SpikingRecurrentSubstrate,
    }

    @classmethod
    def register(cls, name: str, substrate_cls: Type[BaseSubstrate]) -> None:
        """Register an additional substrate class under ``name``."""
        if not issubclass(substrate_cls, BaseSubstrate):
            raise TypeError("substrate classes must subclass BaseSubstrate")
        cls._classes[name] = substrate_cls

    @classmethod
    def list_substrates(cls) -> List[str]:
        """Names of all available substrates."""
        return sorted(cls._classes)

    @classmethod
    def default_config(cls, name: str, input_size: int, seed: int = 0) -> SubstrateConfig:
        """The default configuration the registry would build ``name`` with."""
        if name not in cls._classes:
            raise ValueError(f"unknown substrate {name!r}; available: {cls.list_substrates()}")
        return SubstrateConfig(
            name=name, input_size=input_size,
            state_size=_DEFAULT_STATE_SIZE.get(name, 64), seed=seed, params={})

    @classmethod
    def validate_config(cls, name: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate (and normalise) a config dict for substrate ``name``."""
        if name not in cls._classes:
            raise ValueError(f"unknown substrate {name!r}; available: {cls.list_substrates()}")
        config = dict(config or {})
        for key in ("input_size", "state_size", "seed"):
            if key in config:
                value = int(config[key])
                if key != "seed" and value <= 0:
                    raise ValueError(f"{key} must be positive, got {value}")
                config[key] = value
        return config

    @classmethod
    def create(cls, name: str, input_size: int, state_size: Optional[int] = None,
               seed: int = 0, **params: Any) -> BaseSubstrate:
        """Instantiate substrate ``name`` (raises ``ValueError`` if unknown)."""
        if name not in cls._classes:
            raise ValueError(f"unknown substrate {name!r}; available: {cls.list_substrates()}")
        cls.validate_config(name, {"input_size": input_size,
                                   "state_size": state_size or 1, "seed": seed})
        if state_size is None:
            state_size = _DEFAULT_STATE_SIZE.get(name, 64)
        return cls._classes[name](input_size=input_size, state_size=state_size,
                                  seed=seed, **params)

    @classmethod
    def create_from_config(cls, config: SubstrateConfig) -> BaseSubstrate:
        """Instantiate a substrate from a saved :class:`SubstrateConfig`."""
        return cls.create(config.name, input_size=config.input_size,
                          state_size=config.state_size, seed=config.seed,
                          **dict(config.params))
