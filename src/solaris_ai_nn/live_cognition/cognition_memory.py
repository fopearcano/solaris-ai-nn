"""Live cognition memory -- append-only local metadata; false starts preserved.

:class:`LiveCognitionMemory` persists cognition-trace records as local metadata only:
a JSON snapshot, an append-only JSONL history, and a Markdown index. It preserves
weak, rejected, contradicted, contaminated, and inconclusive traces -- false starts
are never deleted -- every promoted trace links to evidence, and the memory never
stores secrets/private data as a trace identity.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

MEMORY_FILENAME = "LIVE_COGNITION_MEMORY.json"
HISTORY_FILENAME = "LIVE_COGNITION_HISTORY.jsonl"
INDEX_FILENAME = "LIVE_COGNITION_INDEX.md"

_SECRET_MARKERS = ("password", "secret", "api key", "api_key", "credential",
                   "token=", "private message")


@dataclass
class LiveCognitionRecord:
    """One operational cognition-trace record (active, weak, rejected, etc.)."""

    trace_id: str
    kind: str
    status: str
    run_id: str = ""
    linked_sign_ids: List[str] = field(default_factory=list)
    linked_concept_ids: List[str] = field(default_factory=list)
    uncertainty: float = 1.0
    prediction_outcome: str = ""
    supporting_refs: List[str] = field(default_factory=list)
    contradicting_refs: List[str] = field(default_factory=list)
    contamination_findings: List[str] = field(default_factory=list)
    # Membrane ancestry refs (Prompt 73): impression/sign/concept ids this
    # trace traces back to. Empty when the membrane is absent.
    ancestry_refs: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def safe_trace_id(self) -> str:
        low = str(self.trace_id).lower()
        if any(m in low for m in _SECRET_MARKERS):
            return f"trace_redacted_{abs(hash(self.trace_id)) % 100000:05d}"
        return self.trace_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.safe_trace_id(), "kind": self.kind,
            "status": self.status, "run_id": self.run_id,
            "linked_sign_ids": list(self.linked_sign_ids),
            "linked_concept_ids": list(self.linked_concept_ids),
            "uncertainty": round(self.uncertainty, 3),
            "prediction_outcome": self.prediction_outcome,
            "supporting_refs": self.supporting_refs[:50],
            "contradicting_refs": self.contradicting_refs[:50],
            "contamination_findings": list(self.contamination_findings),
            "ancestry_refs": list(self.ancestry_refs),
            "is_live_readonly": True, "implies_reasoning": False,
            "implies_understanding": False, "created_at": self.created_at,
            "note": "operational sign-based anticipation/relation record linked "
                    "to evidence; not reasoning or understanding",
        }


@dataclass
class CognitionMemoryIndex:
    """A lightweight index over the stored cognition records."""

    records: List[LiveCognitionRecord] = field(default_factory=list)

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for r in self.records:
            out[r.status] = out.get(r.status, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "live_cognition_record_count": len(self.records),
            "by_status": self.counts(),
            "promoted_count": self.counts().get("useful", 0)
            + self.counts().get("stable", 0),
            "records": [r.to_dict() for r in self.records],
            "note": "append-only; weak/rejected/contradicted/contaminated/"
                    "inconclusive traces are all preserved; cognition memory is "
                    "local metadata only and never stores secrets as identity",
        }


@dataclass
class LiveCognitionMemory:
    """Append-only local cognition memory (metadata only; never deletes)."""

    state_dir: str = ".solaris_ai_nn_live"
    records: List[LiveCognitionRecord] = field(default_factory=list)

    @property
    def _dir(self) -> str:
        return os.path.join(self.state_dir, "cognition", "traces")

    @property
    def memory_path(self) -> str:
        return os.path.join(self._dir, MEMORY_FILENAME)

    @property
    def history_path(self) -> str:
        return os.path.join(self._dir, HISTORY_FILENAME)

    @property
    def index_path(self) -> str:
        return os.path.join(self._dir, INDEX_FILENAME)

    def load(self) -> "LiveCognitionMemory":
        if os.path.isfile(self.memory_path):
            try:
                with open(self.memory_path, encoding="utf-8") as fh:
                    data = json.load(fh)
                for d in data.get("records", []):
                    self.records.append(self._record_from_dict(d))
            except Exception:
                pass
        return self

    def add(self, record: LiveCognitionRecord) -> LiveCognitionRecord:
        if record.status in ("useful", "stable") and not record.supporting_refs:
            # A promoted trace must link to evidence; downgrade if it does not.
            record.status = "inconclusive"
            record.contamination_findings.append(
                "promoted trace had no supporting evidence; downgraded")
        self.records.append(record)
        return record

    def index(self) -> CognitionMemoryIndex:
        return CognitionMemoryIndex(records=list(self.records))

    def write(self) -> Dict[str, str]:
        os.makedirs(self._dir, exist_ok=True)
        index = self.index()
        with open(self.memory_path, "w", encoding="utf-8") as fh:
            json.dump(index.to_dict(), fh, indent=2, default=str)
        with open(self.history_path, "a", encoding="utf-8") as fh:
            for r in self.records:
                fh.write(json.dumps(r.to_dict(), default=str) + "\n")
        with open(self.index_path, "w", encoding="utf-8") as fh:
            fh.write(self._render_index(index))
        return {"memory": self.memory_path, "history": self.history_path,
                "index": self.index_path}

    def _render_index(self, index: CognitionMemoryIndex) -> str:
        lines = ["# Live Cognition Memory Index", "",
                 f"- records: {index.to_dict()['live_cognition_record_count']}",
                 f"- by status: {index.counts()}", "",
                 "| trace id | kind | status | uncertainty | prediction |",
                 "| --- | --- | --- | --- | --- |"]
        for r in index.records:
            lines.append(f"| {r.safe_trace_id()} | {r.kind} | {r.status} | "
                         f"{r.uncertainty:.2f} | "
                         f"{r.prediction_outcome or '-'} |")
        lines += ["", "_Append-only local metadata. Weak, rejected, "
                  "contradicted, contaminated, and inconclusive traces are all "
                  "preserved; false starts are never deleted. Cognition traces "
                  "are operational anticipation/relation records and do not "
                  "imply reasoning, understanding, or consciousness._"]
        return "\n".join(lines) + "\n"

    @staticmethod
    def _record_from_dict(d: Dict[str, Any]) -> LiveCognitionRecord:
        return LiveCognitionRecord(
            trace_id=d.get("trace_id", ""), kind=d.get("kind", ""),
            status=d.get("status", "unknown"), run_id=d.get("run_id", ""),
            linked_sign_ids=list(d.get("linked_sign_ids", []) or []),
            linked_concept_ids=list(d.get("linked_concept_ids", []) or []),
            uncertainty=float(d.get("uncertainty", 1.0) or 1.0),
            prediction_outcome=d.get("prediction_outcome", ""),
            supporting_refs=list(d.get("supporting_refs", []) or []),
            contradicting_refs=list(d.get("contradicting_refs", []) or []),
            contamination_findings=list(d.get("contamination_findings", [])
                                        or []),
            created_at=float(d.get("created_at", time.time()) or time.time()))
