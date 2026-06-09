"""Reservoir-computing core: ESN substrate, linear readout, online learning."""

from .esn import ESN  # noqa: F401
from .modulation import LogosModulator  # noqa: F401
from .online_learning import DeltaRuleLearner  # noqa: F401
from .readout import LinearReadout  # noqa: F401
from .state import StateSnapshot, snapshot_state, state_drift  # noqa: F401

__all__ = [
    "ESN",
    "LinearReadout",
    "DeltaRuleLearner",
    "LogosModulator",
    "StateSnapshot",
    "snapshot_state",
    "state_drift",
]
