"""Desire memory -- append-only persistence of valence/pushes/desires/outcomes.

The :class:`DesireMemoryStore` writes append-only JSONL records. Failed and blocked
desires, no-op decisions, and safety/governance blocks are all preserved -- never
deleted.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_FILES = {
    "valence": "valence.jsonl",
    "push": "pushes.jsonl",
    "desire": "desires.jsonl",
    "internal_action": "internal_actions.jsonl",
    "outcome": "outcomes.jsonl",
}


@dataclass
class DesireMemoryRecord:
    record_type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"record_type": self.record_type, "timestamp": self.timestamp,
                "payload": self.payload}


@dataclass
class DesireTraceIndex:
    counts: Dict[str, int] = field(default_factory=dict)
    blocked_desire_ids: List[str] = field(default_factory=list)
    failed_desire_ids: List[str] = field(default_factory=list)
    no_op_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"counts": dict(self.counts),
                "blocked_desire_count": len(self.blocked_desire_ids),
                "failed_desire_count": len(self.failed_desire_ids),
                "no_op_count": self.no_op_count}


@dataclass
class DesireMemoryStore:
    """Append-only store for desire traces (failures/blocks/no-ops preserved)."""

    state_dir: str = ".solaris_ai_nn_desire"
    index: DesireTraceIndex = field(default_factory=DesireTraceIndex)
    persist: bool = True

    def _append(self, record_type: str, payload: Dict[str, Any]) -> None:
        self.index.counts[record_type] = self.index.counts.get(
            record_type, 0) + 1
        if record_type == "desire":
            status = payload.get("status", "")
            if status == "blocked_by_safety":
                self.index.blocked_desire_ids.append(payload.get("desire_id"))
            elif status == "failed":
                self.index.failed_desire_ids.append(payload.get("desire_id"))
        if record_type == "internal_action" and payload.get("kind") == "no_op":
            self.index.no_op_count += 1
        if not self.persist:
            return
        filename = _FILES.get(record_type)
        if filename is None:
            return
        os.makedirs(self.state_dir, exist_ok=True)
        with open(os.path.join(self.state_dir, filename), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps(
                DesireMemoryRecord(record_type, payload).to_dict(),
                default=str) + "\n")

    def record_valence(self, payload: Dict[str, Any]) -> None:
        self._append("valence", payload)

    def record_push(self, payload: Dict[str, Any]) -> None:
        self._append("push", payload)

    def record_desire(self, payload: Dict[str, Any]) -> None:
        self._append("desire", payload)

    def record_internal_action(self, payload: Dict[str, Any]) -> None:
        self._append("internal_action", payload)

    def record_outcome(self, payload: Dict[str, Any]) -> None:
        self._append("outcome", payload)

    def write_index(self) -> Optional[str]:
        if not self.persist:
            return None
        os.makedirs(self.state_dir, exist_ok=True)
        path = os.path.join(self.state_dir, "desire_index.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.index.to_dict(), fh, indent=2, default=str)
        return path

    def read_records(self, record_type: str) -> List[Dict[str, Any]]:
        filename = _FILES.get(record_type)
        if filename is None:
            return []
        path = os.path.join(self.state_dir, filename)
        if not os.path.isfile(path):
            return []
        out: List[Dict[str, Any]] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def snapshot(self) -> Dict[str, Any]:
        return self.index.to_dict()
