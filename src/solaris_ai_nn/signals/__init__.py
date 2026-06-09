"""Canonical Solaris signal vocabulary, encoder, and adapters.

Public surface:

* :mod:`canonical` -- the dataclass signal types (Stimulus, Push, ... ).
* :class:`encoding.EventEncoder` -- signal -> numeric feature vector.
* :mod:`adapters` -- signal <-> dict conversion (the bridge seam).
"""

from .adapters import (  # noqa: F401
    SolarisSignalAdapter,
    extract_payload,
    extract_signal_type,
    from_nn_action,
    from_nn_desire,
    to_nn_signal,
)
from .canonical import (  # noqa: F401
    Action,
    Desire,
    LogosTension,
    MapUpdate,
    MeaningEvent,
    Push,
    Reaction,
    Signal,
    Stimulus,
)
from .encoding import EventEncoder  # noqa: F401

__all__ = [
    "Signal",
    "Stimulus",
    "Push",
    "Desire",
    "Action",
    "Reaction",
    "MeaningEvent",
    "MapUpdate",
    "LogosTension",
    "EventEncoder",
    "SolarisSignalAdapter",
    "to_nn_signal",
    "from_nn_action",
    "from_nn_desire",
    "extract_signal_type",
    "extract_payload",
]
