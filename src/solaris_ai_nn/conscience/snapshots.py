"""Conscience snapshots -- one consistent, replayable picture of the runtime.

A :class:`ConscienceSnapshot` captures the orchestrator's context, spine,
bus, registry, lifecycle, scheduler, safety, and (optionally) integration
health at a single point in time. The :class:`SnapshotBuilder` builds these
and persists them as JSON under the state directory so a long run can be
inspected, diffed, and resumed-for-audit later.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ConscienceSnapshot:
    """A single consistent picture of the runtime."""

    snapshot_id: str
    run_id: Optional[str]
    step: int
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "run_id": self.run_id,
            "step": self.step,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }


@dataclass
class SnapshotBuilder:
    """Builds and persists consistent runtime snapshots."""

    state_dir: Optional[str] = None
    history: List[ConscienceSnapshot] = field(default_factory=list, init=False)

    def build(self, orchestrator: Any,
              health_monitor: Any = None) -> ConscienceSnapshot:
        """Capture one consistent snapshot of the orchestrator."""
        try:
            payload = orchestrator.snapshot()
        except Exception as exc:
            payload = {"error": f"snapshot failed: {exc}"}
        if health_monitor is not None:
            try:
                payload["integration_health"] = health_monitor.check(
                    orchestrator).to_dict()
            except Exception:
                pass
        ctx = getattr(orchestrator, "context", None)
        snapshot = ConscienceSnapshot(
            snapshot_id=f"SNAP_{uuid.uuid4().hex[:10]}",
            run_id=getattr(ctx, "run_id", None),
            step=getattr(orchestrator, "step_count", 0),
            payload=payload)
        self.history.append(snapshot)
        self.history = self.history[-200:]
        return snapshot

    def persist(self, snapshot: ConscienceSnapshot,
                state_dir: Optional[str] = None) -> Optional[str]:
        """Write the snapshot to JSON; return the path (or None)."""
        base = state_dir or self.state_dir
        if not base:
            return None
        directory = Path(base) / "snapshots"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{snapshot.snapshot_id}.json"
        path.write_text(json.dumps(snapshot.to_dict(), indent=2, default=str),
                        encoding="utf-8")
        return str(path)

    def build_and_persist(self, orchestrator: Any,
                          health_monitor: Any = None,
                          state_dir: Optional[str] = None,
                          ) -> ConscienceSnapshot:
        snapshot = self.build(orchestrator, health_monitor)
        target = state_dir or self.state_dir \
            or getattr(getattr(orchestrator, "context", None), "state_dir",
                       None)
        snapshot.payload["snapshot_path"] = self.persist(snapshot, target)
        return snapshot

    def latest(self) -> Optional[ConscienceSnapshot]:
        return self.history[-1] if self.history else None

    def snapshot(self) -> Dict[str, Any]:
        return {
            "snapshot_count": len(self.history),
            "latest_id": self.history[-1].snapshot_id if self.history else None,
        }
