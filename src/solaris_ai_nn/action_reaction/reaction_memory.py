"""Reaction memory -- append-only persistence of the action-reaction loop.

The :class:`ReactionMemoryStore` writes append-only JSONL records. Failed, blocked,
no-effect, and inhibited actions are all preserved -- never deleted.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_FILES = {
    "action": "actions.jsonl",
    "reaction": "reactions.jsonl",
    "consequence": "consequences.jsonl",
    "effect": "effects.jsonl",
    "habit": "habits.jsonl",
    "inhibition": "inhibitions.jsonl",
    "policy_update": "policy_updates.jsonl",
}


@dataclass
class ReactionMemoryRecord:
    record_type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"record_type": self.record_type, "timestamp": self.timestamp,
                "payload": self.payload}


@dataclass
class ReactionTraceIndex:
    counts: Dict[str, int] = field(default_factory=dict)
    blocked_action_ids: List[str] = field(default_factory=list)
    no_effect_action_ids: List[str] = field(default_factory=list)
    no_op_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"counts": dict(self.counts),
                "blocked_action_count": len(self.blocked_action_ids),
                "no_effect_action_count": len(self.no_effect_action_ids),
                "no_op_count": self.no_op_count}


@dataclass
class ReactionMemoryStore:
    """Append-only store for the action-reaction loop (negatives preserved)."""

    state_dir: str = ".solaris_ai_nn_action_reaction"
    index: ReactionTraceIndex = field(default_factory=ReactionTraceIndex)
    persist: bool = True

    def _append(self, record_type: str, payload: Dict[str, Any]) -> None:
        self.index.counts[record_type] = self.index.counts.get(
            record_type, 0) + 1
        if record_type == "action":
            if payload.get("status") == "blocked" or payload.get("is_forbidden"):
                self.index.blocked_action_ids.append(payload.get("action_id"))
            if payload.get("kind") == "no_op":
                self.index.no_op_count += 1
        if record_type == "reaction" and payload.get("kind") == "no_effect":
            self.index.no_effect_action_ids.append(payload.get("action_ref"))
        if not self.persist:
            return
        filename = _FILES.get(record_type)
        if filename is None:
            return
        os.makedirs(self.state_dir, exist_ok=True)
        with open(os.path.join(self.state_dir, filename), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps(
                ReactionMemoryRecord(record_type, payload).to_dict(),
                default=str) + "\n")

    def record_action(self, payload: Dict[str, Any]) -> None:
        self._append("action", payload)

    def record_reaction(self, payload: Dict[str, Any]) -> None:
        self._append("reaction", payload)

    def record_consequence(self, payload: Dict[str, Any]) -> None:
        self._append("consequence", payload)

    def record_effect(self, payload: Dict[str, Any]) -> None:
        self._append("effect", payload)

    def record_habit(self, payload: Dict[str, Any]) -> None:
        self._append("habit", payload)

    def record_inhibition(self, payload: Dict[str, Any]) -> None:
        self._append("inhibition", payload)

    def record_policy_update(self, payload: Dict[str, Any]) -> None:
        self._append("policy_update", payload)

    def write_index(self) -> Optional[str]:
        if not self.persist:
            return None
        os.makedirs(self.state_dir, exist_ok=True)
        path = os.path.join(self.state_dir, "action_reaction_index.json")
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
