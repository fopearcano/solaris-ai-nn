"""Sign memory -- append-only persistence of signs, relations, and utterances.

The :class:`SignMemoryStore` writes append-only JSONL records under the state
directory. Signs are never deleted: decay, split, merge, and rejection are
recorded as new state records, and ambiguous signs are preserved as historical
evidence.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SignMemoryRecord:
    """One append-only memory record (sign, relation, utterance, state change)."""

    record_type: str  # "sign" | "sign_state" | "relation" | "utterance"
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"record_type": self.record_type, "timestamp": self.timestamp,
                "payload": self.payload}


@dataclass
class SignMemoryIndex:
    """An in-memory index over the latest known state of each sign."""

    signs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    relations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    utterance_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        statuses: Dict[str, int] = {}
        for s in self.signs.values():
            statuses[s.get("status", "unknown")] = statuses.get(
                s.get("status", "unknown"), 0) + 1
        return {
            "sign_count": len(self.signs),
            "relation_count": len(self.relations),
            "utterance_count": len(self.utterance_ids),
            "status_distribution": statuses,
            "sign_codes": sorted(s.get("sign_code", sid)
                                 for sid, s in self.signs.items()),
        }


@dataclass
class SignMemoryStore:
    """Append-only store for signs, sign relations, and utterances."""

    state_dir: str = ".solaris_ai_nn_semiogenesis"
    index: SignMemoryIndex = field(default_factory=SignMemoryIndex)
    persist: bool = True

    def _path(self, name: str) -> str:
        return os.path.join(self.state_dir, name)

    def _append(self, filename: str, record: Dict[str, Any]) -> None:
        if not self.persist:
            return
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._path(filename), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")

    def record_sign(self, sign_dict: Dict[str, Any]) -> None:
        self._append("signs.jsonl",
                     SignMemoryRecord("sign", sign_dict).to_dict())
        sid = sign_dict.get("sign_id")
        if sid:
            self.index.signs[sid] = sign_dict

    def record_sign_state(self, sign_id: str, status: str,
                          detail: Dict[str, Any]) -> None:
        """Record a state transition (decay/split/merge/reject) as new state."""
        payload = {"sign_id": sign_id, "status": status, **detail}
        self._append("signs.jsonl",
                     SignMemoryRecord("sign_state", payload).to_dict())
        if sign_id in self.index.signs:
            self.index.signs[sign_id]["status"] = status

    def record_relation(self, relation_dict: Dict[str, Any]) -> None:
        self._append("sign_relations.jsonl",
                     SignMemoryRecord("relation", relation_dict).to_dict())
        rid = relation_dict.get("pattern_id") or relation_dict.get("relation_id")
        if rid:
            self.index.relations[rid] = relation_dict

    def record_utterance(self, utterance_dict: Dict[str, Any]) -> None:
        self._append("utterances.jsonl",
                     SignMemoryRecord("utterance", utterance_dict).to_dict())
        uid = utterance_dict.get("utterance_id")
        if uid and uid not in self.index.utterance_ids:
            self.index.utterance_ids.append(uid)

    def write_index(self) -> Optional[str]:
        if not self.persist:
            return None
        os.makedirs(self.state_dir, exist_ok=True)
        path = self._path("sign_index.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.index.to_dict(), fh, indent=2, default=str)
        return path

    def sign_history(self, sign_id: str) -> List[Dict[str, Any]]:
        """Read back all append-only records for a sign (history preserved)."""
        path = self._path("signs.jsonl")
        if not os.path.isfile(path):
            return []
        out: List[Dict[str, Any]] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("payload", {}).get("sign_id") == sign_id:
                    out.append(rec)
        return out

    def snapshot(self) -> Dict[str, Any]:
        return self.index.to_dict()
