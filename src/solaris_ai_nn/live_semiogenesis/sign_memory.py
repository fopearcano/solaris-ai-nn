"""Live sign memory -- append-only local metadata; false starts preserved.

:class:`LiveSignMemory` persists private sign records as local metadata only: a JSON
snapshot, an append-only JSONL history, and a Markdown index. It preserves sign
candidates, weak signs, rejected signs, and contaminated signs -- false starts are
never deleted -- every born sign links to concept evidence, and the memory never
stores private data or secrets as a sign token.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

MEMORY_FILENAME = "LIVE_SIGN_MEMORY.json"
HISTORY_FILENAME = "LIVE_SIGN_HISTORY.jsonl"
INDEX_FILENAME = "LIVE_SIGN_INDEX.md"

_SECRET_MARKERS = ("password", "secret", "api key", "api_key", "credential",
                   "token=", "private message")


@dataclass
class LiveSignRecord:
    """One operational private sign record (born, weak, rejected, etc.)."""

    sign_id: str
    private_token: str
    status: str
    run_id: str = ""
    linked_concept_ids: List[str] = field(default_factory=list)
    utility_score: float = 0.0
    source_distribution: Dict[str, int] = field(default_factory=dict)
    supporting_refs: List[str] = field(default_factory=list)
    contradicting_refs: List[str] = field(default_factory=list)
    contamination_findings: List[str] = field(default_factory=list)
    birth_gate_status: str = ""
    debug_alias: str = ""
    # Membrane ancestry refs (Prompt 73): impression/receptor/source-event ids
    # this sign's concept(s) trace back to. Empty when the membrane is absent.
    ancestry_refs: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def sanitized_token(self) -> str:
        low = str(self.private_token).lower()
        if any(m in low for m in _SECRET_MARKERS):
            return f"sig_live_redacted_{abs(hash(self.sign_id)) % 100000:05d}"
        return self.private_token

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_id": self.sign_id, "private_token": self.sanitized_token(),
            "status": self.status, "run_id": self.run_id,
            "linked_concept_ids": list(self.linked_concept_ids),
            "utility_score": round(self.utility_score, 3),
            "source_distribution": dict(self.source_distribution),
            "supporting_refs": self.supporting_refs[:50],
            "contradicting_refs": self.contradicting_refs[:50],
            "contamination_findings": list(self.contamination_findings),
            "birth_gate_status": self.birth_gate_status,
            "debug_alias": self.debug_alias,
            "ancestry_refs": list(self.ancestry_refs),
            "debug_alias_is_ground_truth": False,
            "is_live_readonly": True, "implies_language_understanding": False,
            "created_at": self.created_at,
            "note": "operational private sign record linked to concept evidence; "
                    "not language understanding",
        }


@dataclass
class SignMemoryIndex:
    """A lightweight index over the stored sign records."""

    records: List[LiveSignRecord] = field(default_factory=list)

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for r in self.records:
            out[r.status] = out.get(r.status, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "live_sign_record_count": len(self.records),
            "by_status": self.counts(),
            "born_count": self.counts().get("born", 0),
            "records": [r.to_dict() for r in self.records],
            "note": "append-only; candidates/weak/rejected/contaminated signs "
                    "are all preserved; sign memory is local metadata only and "
                    "never stores private data/secrets as a token",
        }


@dataclass
class LiveSignMemory:
    """Append-only local sign memory (metadata only; never deletes)."""

    state_dir: str = ".solaris_ai_nn_live"
    records: List[LiveSignRecord] = field(default_factory=list)

    @property
    def _dir(self) -> str:
        return os.path.join(self.state_dir, "semiogenesis", "signs")

    @property
    def memory_path(self) -> str:
        return os.path.join(self._dir, MEMORY_FILENAME)

    @property
    def history_path(self) -> str:
        return os.path.join(self._dir, HISTORY_FILENAME)

    @property
    def index_path(self) -> str:
        return os.path.join(self._dir, INDEX_FILENAME)

    def load(self) -> "LiveSignMemory":
        if os.path.isfile(self.memory_path):
            try:
                with open(self.memory_path, encoding="utf-8") as fh:
                    data = json.load(fh)
                for d in data.get("records", []):
                    self.records.append(self._record_from_dict(d))
            except Exception:
                pass
        return self

    def add(self, record: LiveSignRecord) -> LiveSignRecord:
        if record.status == "born" and not record.linked_concept_ids:
            # A born sign must link to concept evidence; downgrade if it does not.
            record.status = "inconclusive"
            record.contamination_findings.append(
                "born sign had no linked concept evidence; downgraded")
        self.records.append(record)
        return record

    def index(self) -> SignMemoryIndex:
        return SignMemoryIndex(records=list(self.records))

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

    def _render_index(self, index: SignMemoryIndex) -> str:
        lines = ["# Live Sign Memory Index", "",
                 f"- records: {index.to_dict()['live_sign_record_count']}",
                 f"- by status: {index.counts()}", "",
                 "| sign id | status | private token | utility | concepts |",
                 "| --- | --- | --- | --- | --- |"]
        for r in index.records:
            lines.append(f"| {r.sign_id} | {r.status} | {r.sanitized_token()} | "
                         f"{r.utility_score:.2f} | "
                         f"{len(r.linked_concept_ids)} |")
        lines += ["", "_Append-only local metadata. Candidates, weak, rejected, "
                  "and contaminated signs are all preserved; false starts are "
                  "never deleted. Private signs are operational reference "
                  "structures and do not imply language or understanding. Tokens "
                  "never store private data or secrets._"]
        return "\n".join(lines) + "\n"

    @staticmethod
    def _record_from_dict(d: Dict[str, Any]) -> LiveSignRecord:
        return LiveSignRecord(
            sign_id=d.get("sign_id", ""),
            private_token=d.get("private_token", ""),
            status=d.get("status", "unknown"), run_id=d.get("run_id", ""),
            linked_concept_ids=list(d.get("linked_concept_ids", []) or []),
            utility_score=float(d.get("utility_score", 0.0) or 0.0),
            source_distribution=dict(d.get("source_distribution", {}) or {}),
            supporting_refs=list(d.get("supporting_refs", []) or []),
            contradicting_refs=list(d.get("contradicting_refs", []) or []),
            contamination_findings=list(d.get("contamination_findings", [])
                                        or []),
            birth_gate_status=d.get("birth_gate_status", ""),
            debug_alias=d.get("debug_alias", ""),
            created_at=float(d.get("created_at", time.time()) or time.time()))
