"""Live concept memory -- append-only local metadata; false starts preserved.

:class:`LiveConceptMemory` persists proto-concept records as local metadata only:
a JSON snapshot, an append-only JSONL history, and a Markdown index. It preserves
candidates, weak concepts, rejected concepts, and contaminated concepts -- false
starts are never deleted -- and every record links to its supporting and
contradicting evidence.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

MEMORY_FILENAME = "LIVE_CONCEPT_MEMORY.json"
HISTORY_FILENAME = "LIVE_CONCEPT_HISTORY.jsonl"
INDEX_FILENAME = "LIVE_CONCEPT_INDEX.md"


@dataclass
class LiveConceptRecord:
    """One operational proto-concept record (born, weak, rejected, etc.)."""

    concept_id: str
    feature_signature: str
    status: str
    run_id: str = ""
    stability_score: float = 0.0
    recurrence_count: int = 0
    source_distribution: Dict[str, int] = field(default_factory=dict)
    supporting_event_ids: List[str] = field(default_factory=list)
    contradicting_event_ids: List[str] = field(default_factory=list)
    contamination_findings: List[str] = field(default_factory=list)
    birth_gate_status: str = ""
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "feature_signature": self.feature_signature,
            "status": self.status, "run_id": self.run_id,
            "stability_score": round(self.stability_score, 3),
            "recurrence_count": self.recurrence_count,
            "source_distribution": dict(self.source_distribution),
            "supporting_event_ids": self.supporting_event_ids[:50],
            "contradicting_event_ids": self.contradicting_event_ids[:50],
            "contamination_findings": list(self.contamination_findings),
            "birth_gate_status": self.birth_gate_status,
            "created_at": self.created_at,
            "is_live_readonly": True,
            "implies_understanding": False,
            "note": "operational feature-stability record linked to evidence; "
                    "not a concept of understanding",
        }


@dataclass
class ConceptMemoryIndex:
    """A lightweight index over the stored concept records."""

    records: List[LiveConceptRecord] = field(default_factory=list)

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for r in self.records:
            out[r.status] = out.get(r.status, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "live_concept_record_count": len(self.records),
            "by_status": self.counts(),
            "born_count": self.counts().get("born", 0),
            "records": [r.to_dict() for r in self.records],
            "note": "append-only; candidates/weak/rejected/contaminated records "
                    "are all preserved; concept memory is local metadata only",
        }


@dataclass
class LiveConceptMemory:
    """Append-only local concept memory (metadata only; never deletes)."""

    state_dir: str = ".solaris_ai_nn_live"
    records: List[LiveConceptRecord] = field(default_factory=list)

    @property
    def _dir(self) -> str:
        return os.path.join(self.state_dir, "ontogenesis", "concepts")

    @property
    def memory_path(self) -> str:
        return os.path.join(self._dir, MEMORY_FILENAME)

    @property
    def history_path(self) -> str:
        return os.path.join(self._dir, HISTORY_FILENAME)

    @property
    def index_path(self) -> str:
        return os.path.join(self._dir, INDEX_FILENAME)

    def load(self) -> "LiveConceptMemory":
        """Load existing records (read-only) so history stays append-only."""
        if os.path.isfile(self.memory_path):
            try:
                with open(self.memory_path, encoding="utf-8") as fh:
                    data = json.load(fh)
                for d in data.get("records", []):
                    self.records.append(self._record_from_dict(d))
            except Exception:
                pass
        return self

    def add(self, record: LiveConceptRecord) -> LiveConceptRecord:
        if not record.supporting_event_ids and record.status == "born":
            # A born concept must link to evidence; downgrade if it does not.
            record.status = "inconclusive"
            record.contamination_findings.append(
                "born record had no supporting evidence; downgraded")
        self.records.append(record)
        return record

    def index(self) -> ConceptMemoryIndex:
        return ConceptMemoryIndex(records=list(self.records))

    def write(self) -> Dict[str, str]:
        os.makedirs(self._dir, exist_ok=True)
        index = self.index()
        with open(self.memory_path, "w", encoding="utf-8") as fh:
            json.dump(index.to_dict(), fh, indent=2, default=str)
        # Append-only history: append new records, never rewrite the file.
        with open(self.history_path, "a", encoding="utf-8") as fh:
            for r in self.records:
                fh.write(json.dumps(r.to_dict(), default=str) + "\n")
        with open(self.index_path, "w", encoding="utf-8") as fh:
            fh.write(self._render_index(index))
        return {"memory": self.memory_path, "history": self.history_path,
                "index": self.index_path}

    def _render_index(self, index: ConceptMemoryIndex) -> str:
        lines = ["# Live Concept Memory Index", "",
                 f"- records: {index.to_dict()['live_concept_record_count']}",
                 f"- by status: {index.counts()}", "",
                 "| concept id | status | signature | recurrence | stability |",
                 "| --- | --- | --- | --- | --- |"]
        for r in index.records:
            lines.append(f"| {r.concept_id} | {r.status} | "
                         f"{r.feature_signature} | {r.recurrence_count} | "
                         f"{r.stability_score:.2f} |")
        lines += ["", "_Append-only local metadata. Candidates, weak, rejected, "
                  "and contaminated records are all preserved; false starts are "
                  "never deleted. Proto-concepts are operational feature-"
                  "stability records and do not imply understanding._"]
        return "\n".join(lines) + "\n"

    @staticmethod
    def _record_from_dict(d: Dict[str, Any]) -> LiveConceptRecord:
        return LiveConceptRecord(
            concept_id=d.get("concept_id", ""),
            feature_signature=d.get("feature_signature", ""),
            status=d.get("status", "unknown"), run_id=d.get("run_id", ""),
            stability_score=float(d.get("stability_score", 0.0) or 0.0),
            recurrence_count=int(d.get("recurrence_count", 0) or 0),
            source_distribution=dict(d.get("source_distribution", {}) or {}),
            supporting_event_ids=list(d.get("supporting_event_ids", []) or []),
            contradicting_event_ids=list(
                d.get("contradicting_event_ids", []) or []),
            contamination_findings=list(
                d.get("contamination_findings", []) or []),
            birth_gate_status=d.get("birth_gate_status", ""),
            created_at=float(d.get("created_at", time.time()) or time.time()))
