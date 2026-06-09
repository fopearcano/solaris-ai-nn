"""Canonical Solaris signal vocabulary, encoder, and adapters.

Public surface:

* :mod:`canonical` -- the dataclass signal types (Stimulus, Push, ... ).
* :class:`encoding.EventEncoder` -- signal -> numeric feature vector.
* :mod:`adapters` -- signal <-> dict conversion (the bridge seam).
"""

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
]
