"""Embodiment state aggregation for persistence and the Inner MAP.

`build_embodiment_state` collects the body/world/energy snapshots plus bounded
history summaries into the :class:`EmbodimentState` record that gets persisted
(`embodiment_state.json`) and surfaced through the Inner MAP.
"""

from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List, Optional

from .base import ActionResult, EmbodimentState, SensorReading
from .body import SimulatedBody
from .grid_world import GridWorld


def summarise_sensor_history(readings: Iterable[SensorReading]) -> Dict[str, int]:
    """Count readings by payload (bounded, summary-only)."""
    return dict(Counter(r.payload for r in readings))


def summarise_action_history(results: Iterable[ActionResult]) -> Dict[str, int]:
    """Count results by action name."""
    return dict(Counter(r.action for r in results))


def build_embodiment_state(
    body: SimulatedBody,
    world: GridWorld,
    sensor_history: Optional[List[SensorReading]] = None,
    action_history: Optional[List[ActionResult]] = None,
) -> EmbodimentState:
    """Assemble the aggregate embodiment record."""
    return EmbodimentState(
        body=body.snapshot(),
        world=world.snapshot(),
        energy=body.energy.snapshot(),
        last_action_result=body.last_result.to_dict() if body.last_result else None,
        sensor_history_summary=summarise_sensor_history(sensor_history or []),
        action_history_summary=summarise_action_history(action_history or []),
    )
