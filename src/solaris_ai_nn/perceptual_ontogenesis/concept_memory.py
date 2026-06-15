"""Concept memory -- append-only persistence of atoms, concepts, and relations.

The :class:`ConceptMemoryStore` writes append-only JSONL records under the state
directory. Concepts are never deleted automatically: decay and rejection are
recorded as new state records, and negative / failed / ambiguous concepts are
preserved as historical evidence.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConceptMemoryRecord:
    """One append-only memory record (atom, concept, relation, or state change)."""

    record_type: str  # "atom" | "concept" | "relation" | "concept_state"
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"record_type": self.record_type, "timestamp": self.timestamp,
                "payload": self.payload}


@dataclass
class ConceptMemoryIndex:
    """An in-memory index over the latest known state of each concept."""

    concepts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    relations: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    atom_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        statuses: Dict[str, int] = {}
        for c in self.concepts.values():
            statuses[c.get("status", "unknown")] = statuses.get(
                c.get("status", "unknown"), 0) + 1
        return {
            "concept_count": len(self.concepts),
            "relation_count": len(self.relations),
            "atom_count": len(self.atom_ids),
            "status_distribution": statuses,
            "concept_ids": sorted(self.concepts),
        }


@dataclass
class ConceptMemoryStore:
    """Append-only store for atoms, concepts, relations, and state changes."""

    state_dir: str = ".solaris_ai_nn_ontogenesis"
    index: ConceptMemoryIndex = field(default_factory=ConceptMemoryIndex)
    persist: bool = True

    def _path(self, name: str) -> str:
        return os.path.join(self.state_dir, name)

    def _append(self, filename: str, record: Dict[str, Any]) -> None:
        if not self.persist:
            return
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._path(filename), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, default=str) + "\n")

    def record_atom(self, atom_dict: Dict[str, Any]) -> None:
        self._append("atoms.jsonl",
                     ConceptMemoryRecord("atom", atom_dict).to_dict())
        aid = atom_dict.get("atom_id")
        if aid and aid not in self.index.atom_ids:
            self.index.atom_ids.append(aid)

    def record_concept(self, concept_dict: Dict[str, Any]) -> None:
        """Record a concept's current state (append-only; never overwrites)."""
        self._append("concepts.jsonl",
                     ConceptMemoryRecord("concept", concept_dict).to_dict())
        cid = concept_dict.get("concept_id")
        if cid:
            self.index.concepts[cid] = concept_dict

    def record_concept_state(self, concept_id: str, status: str,
                             detail: Dict[str, Any]) -> None:
        """Record a state transition (e.g. decay/rejection) as new state."""
        payload = {"concept_id": concept_id, "status": status, **detail}
        self._append("concepts.jsonl",
                     ConceptMemoryRecord("concept_state", payload).to_dict())
        if concept_id in self.index.concepts:
            self.index.concepts[concept_id]["status"] = status

    def record_relation(self, relation_dict: Dict[str, Any]) -> None:
        self._append("relations.jsonl",
                     ConceptMemoryRecord("relation", relation_dict).to_dict())
        rid = relation_dict.get("relation_id")
        if rid:
            self.index.relations[rid] = relation_dict

    def write_index(self) -> Optional[str]:
        if not self.persist:
            return None
        os.makedirs(self.state_dir, exist_ok=True)
        path = self._path("concept_index.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.index.to_dict(), fh, indent=2, default=str)
        return path

    def concept_history(self, concept_id: str) -> List[Dict[str, Any]]:
        """Read back all append-only records for a concept (history preserved)."""
        path = self._path("concepts.jsonl")
        if not os.path.isfile(path):
            return []
        out: List[Dict[str, Any]] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if rec.get("payload", {}).get("concept_id") == concept_id:
                    out.append(rec)
        return out

    def snapshot(self) -> Dict[str, Any]:
        return self.index.to_dict()
