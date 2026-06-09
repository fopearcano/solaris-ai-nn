"""RollbackManager -- undo any applied plasticity step.

Every applied step registers a rollback record (its target + old value). Rolling
back routes the old value back through the same :class:`TargetRegistry` that
applied it, then *verifies* the live parameter actually returned to the old
value. Unknown step ids fail gracefully (no exception, a failed result).
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .mutation import (
    APPLIED,
    ROLLED_BACK,
    PlasticityResult,
    PlasticityStep,
    PlasticityTarget,
    TargetRegistry,
)


@dataclass
class RollbackRecord:
    """Stored data needed to undo one applied step."""

    step_id: str
    target: PlasticityTarget
    old_value: Any
    new_value: Any
    applied_ts: float = field(default_factory=time.time)
    rolled_back: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "target": self.target.label(),
            "old_value": self.old_value,
            "new_value": self.new_value,
            "applied_ts": self.applied_ts,
            "rolled_back": self.rolled_back,
        }


def _approx_equal(a: Any, b: Any, tol: float = 1e-6) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)
    return a == b


@dataclass
class RollbackManager:
    """Stores rollback records and restores previous parameter values."""

    records: Dict[str, RollbackRecord] = field(default_factory=dict)
    order: List[str] = field(default_factory=list)

    def register(self, step: PlasticityStep) -> None:
        """Record the data needed to undo an applied ``step``."""
        rec = RollbackRecord(
            step_id=step.step_id,
            target=step.target,
            old_value=step.change.old_value,
            new_value=step.change.new_value,
        )
        self.records[step.step_id] = rec
        self.order.append(step.step_id)

    def rollback(self, step_id: str, target_registry: TargetRegistry) -> PlasticityResult:
        """Restore the previous value for ``step_id`` and verify it took effect."""
        rec = self.records.get(step_id)
        if rec is None:
            return PlasticityResult(
                step_id=step_id, status="rollback_failed", applied=False,
                message=f"unknown plasticity step id {step_id!r}")
        if rec.rolled_back:
            return PlasticityResult(
                step_id=step_id, status="rollback_failed", applied=False,
                message="step already rolled back")
        try:
            target_registry.set(rec.target, rec.old_value)
            restored = target_registry.get(rec.target)
        except (KeyError, ValueError) as exc:
            return PlasticityResult(
                step_id=step_id, status="rollback_failed", applied=False,
                message=f"rollback error: {exc}")

        if not _approx_equal(restored, rec.old_value):
            return PlasticityResult(
                step_id=step_id, status="rollback_failed", applied=False,
                message=f"verification failed: {restored} != {rec.old_value}",
                old_value=rec.new_value, new_value=rec.old_value)

        rec.rolled_back = True
        return PlasticityResult(
            step_id=step_id, status=ROLLED_BACK, applied=True,
            message="rolled back and verified",
            old_value=rec.new_value, new_value=rec.old_value)

    def list_steps(self) -> List[Dict[str, Any]]:
        return [self.records[sid].to_dict() for sid in self.order]

    def last_applied(self) -> Optional[RollbackRecord]:
        """Most recent registered step that has not been rolled back."""
        for sid in reversed(self.order):
            rec = self.records[sid]
            if not rec.rolled_back:
                return rec
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": len(self.records),
            "rolled_back": sum(1 for r in self.records.values() if r.rolled_back),
            "steps": self.list_steps(),
        }
