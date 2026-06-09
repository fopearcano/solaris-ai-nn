"""Bridges to the conceptual Solaris_Ai reference (kept import-free for now)."""

from .signal_bridge import inbound, outbound  # noqa: F401
from .solaris_reference import REFERENCE_MAP, Mapping, describe  # noqa: F401

__all__ = ["REFERENCE_MAP", "Mapping", "describe", "inbound", "outbound"]
