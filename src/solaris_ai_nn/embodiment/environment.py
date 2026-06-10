"""Environment surface of the embodiment package.

The abstract :class:`Environment` contract lives in ``base.py``; the first
concrete world is :class:`GridWorld` (``grid_world.py``). This module is the
stable import point for both, and the place future environments (other worlds,
richer physics -- still simulation-only) will be registered.
"""

from __future__ import annotations

from .base import Environment  # noqa: F401
from .grid_world import GridWorld  # noqa: F401

AVAILABLE_ENVIRONMENTS = {"grid_world": GridWorld}


def create_environment(name: str = "grid_world", **kwargs) -> Environment:
    """Create a registered simulated environment by name."""
    if name not in AVAILABLE_ENVIRONMENTS:
        raise ValueError(f"unknown environment {name!r}; "
                         f"available: {sorted(AVAILABLE_ENVIRONMENTS)}")
    return AVAILABLE_ENVIRONMENTS[name](**kwargs)
