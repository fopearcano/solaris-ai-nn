"""Inner MAP: a structured, persistent self-model of the NN substrate.

This package observes the low-compute neural substrate and exposes an
inspectable model of its current state, boundaries, tendencies, memory, habits,
synthesis history, continuity, and unknowns. It mirrors Solaris_Ai's Inner MAP
concept. It does **not** make the system conscious -- it is self-*observation*,
not self-awareness.
"""

from .boundaries import (  # noqa: F401
    Boundary,
    BoundaryRegistry,
    BoundaryViolation,
)
from .model import (  # noqa: F401
    BoundaryState,
    ContinuityState,
    InnerMapModel,
    MemoryState,
    ModuleState,
    NeuralSubstrateState,
    PlasticityState,
    TendencyState,
    UnknownState,
)
from .observer import InnerMapObserver  # noqa: F401
from .serialization import (  # noqa: F401
    inner_map_from_json,
    inner_map_to_json,
    load_inner_map,
    save_inner_map,
)
from .state_graph import StateGraph, build_default_state_graph  # noqa: F401

__all__ = [
    "InnerMapModel",
    "ModuleState",
    "ContinuityState",
    "NeuralSubstrateState",
    "MemoryState",
    "PlasticityState",
    "BoundaryState",
    "TendencyState",
    "UnknownState",
    "InnerMapObserver",
    "BoundaryRegistry",
    "Boundary",
    "BoundaryViolation",
    "StateGraph",
    "build_default_state_graph",
    "save_inner_map",
    "load_inner_map",
    "inner_map_to_json",
    "inner_map_from_json",
]
