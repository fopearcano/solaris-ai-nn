"""Plasticity audit log -- append-only JSONL record of every mutation event.

Plasticity must never happen silently. Every proposal, rejection, application,
and rollback is written here, to ``plasticity_audit.jsonl`` in the state dir.
This is separate from the continuity log (lifecycle) so plasticity history can be
read on its own, but it carries the same run/session identity.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .mutation import PlasticityResult, PlasticityStep

PROPOSED = "proposed"
REJECTED = "rejected"
APPLIED = "applied"
ROLLBACK = "rollback"
ROLLBACK_FAILED = "rollback_failed"

EVENT_TYPES = frozenset({PROPOSED, REJECTED, APPLIED, ROLLBACK, ROLLBACK_FAILED})


@dataclass
class PlasticityAuditLog:
    """Append-only JSONL log of plasticity events."""

    path: Union[str, Path]
    run_id: str = ""
    session_id: str = ""
    _writer: Any = field(default=None, repr=False, init=False)

    def __post_init__(self) -> None:
        from ..runtime.persistence import JsonlWriter  # local: keep plasticity self-contained

        self.path = Path(self.path)
        self._writer = JsonlWriter(self.path, append=True)

    def _row(self, event_type: str, step: PlasticityStep,
             observed_effect: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "timestamp": time.time(),
            "run_id": self.run_id or step.run_id,
            "session_id": self.session_id or step.session_id,
            "lifetime_step": step.lifetime_step,
            "event_type": event_type,
            "step_id": step.step_id,
            "target": step.target.label(),
            "reason": step.reason,
            "old_value": step.change.old_value,
            "new_value": step.change.new_value,
            "safety_result": step.safety_result,
            "observed_effect": observed_effect if observed_effect is not None else step.observed_effect,
        }

    def log(self, event_type: str, step: PlasticityStep,
            observed_effect: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unknown plasticity event type: {event_type!r}")
        row = self._row(event_type, step, observed_effect)
        self._writer.write(row)
        return row

    def proposed(self, step: PlasticityStep) -> None:
        self.log(PROPOSED, step)

    def rejected(self, step: PlasticityStep) -> None:
        self.log(REJECTED, step)

    def applied(self, step: PlasticityStep) -> None:
        self.log(APPLIED, step)

    def rollback(self, step: PlasticityStep, result: PlasticityResult) -> None:
        event = ROLLBACK if result.applied else ROLLBACK_FAILED
        self.log(event, step, observed_effect={"message": result.message})

    def read_all(self) -> List[Dict[str, Any]]:
        from ..runtime.persistence import read_jsonl  # local: keep plasticity self-contained

        if not Path(self.path).exists():
            return []
        return list(read_jsonl(self.path))

    def tail(self, n: int) -> List[Dict[str, Any]]:
        return self.read_all()[-n:]

    def count(self) -> int:
        return len(self.read_all())

    def close(self) -> None:
        self._writer.close()
