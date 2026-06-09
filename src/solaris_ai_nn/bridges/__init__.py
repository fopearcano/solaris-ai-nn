"""Bridges to the conceptual Solaris_Ai reference (kept import-free for now).

* :class:`SolarisNeuralBridge` -- the runtime compatibility layer that consumes
  Solaris-style signals and runs them through the neural substrate.
* :mod:`signal_bridge` -- low-level inbound/outbound dict translation helpers.
* :mod:`solaris_reference` -- the in-code concept map to the reference repo.
"""

from .neural_bridge import SolarisNeuralBridge  # noqa: F401
from .signal_bridge import inbound, outbound  # noqa: F401
from .solaris_reference import REFERENCE_MAP, Mapping, describe  # noqa: F401

__all__ = [
    "SolarisNeuralBridge",
    "REFERENCE_MAP",
    "Mapping",
    "describe",
    "inbound",
    "outbound",
]
