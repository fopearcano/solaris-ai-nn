"""Substrate laboratory: interchangeable low-compute neural substrates.

All substrates consume the same encoded Solaris signal vectors and expose the
same interface (:class:`BaseSubstrate`): ESN baseline, Liquid-State-inspired,
and a simple spiking recurrent substrate. None are trained internally -- the
linear readout remains the only adaptive layer. NumPy enters the project here.
"""

from .base import (  # noqa: F401
    BaseSubstrate,
    SubstrateConfig,
    SubstrateMetrics,
    SubstrateState,
)
from .comparison import ComparisonReport, ComparisonRow, energy_proxy  # noqa: F401
from .esn_substrate import EchoStateSubstrate  # noqa: F401
from .liquid_state import LiquidStateSubstrate  # noqa: F401
from .registry import SubstrateRegistry  # noqa: F401
from .spiking_recurrent import SpikingRecurrentSubstrate  # noqa: F401
from .switching import SubstrateSwitcher, SwitchRecord  # noqa: F401

__all__ = [
    "BaseSubstrate",
    "SubstrateConfig",
    "SubstrateState",
    "SubstrateMetrics",
    "EchoStateSubstrate",
    "LiquidStateSubstrate",
    "SpikingRecurrentSubstrate",
    "SubstrateRegistry",
    "SubstrateSwitcher",
    "SwitchRecord",
    "ComparisonReport",
    "ComparisonRow",
    "energy_proxy",
]
