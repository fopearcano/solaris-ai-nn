"""Tester feedback ledger -- the append-only, local QA record.

:class:`TesterFeedbackLedger` appends one :class:`FeedbackLedgerEntry` per submission to
a JSONL file (never deleting or silently editing prior entries), records redactions,
and regenerates the JSON aggregate and Markdown index. The ledger is local only.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


class FeedbackEntryStatus:
    NEW = "new"
    TRIAGED = "triaged"
    NEEDS_REPRODUCTION = "needs_reproduction"
    ACCEPTED = "accepted"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    RESOLVED = "resolved"
    UNKNOWN = "unknown"

    ALL = (NEW, TRIAGED, NEEDS_REPRODUCTION, ACCEPTED, DEFERRED, REJECTED,
           DUPLICATE, RESOLVED, UNKNOWN)


@dataclass
class FeedbackLedgerEntry:
    """One append-only ledger entry."""

    feedback_id: str
    feedback_type: str = "feedback"
    timestamp: str = ""
    tester_alias: str = "anonymous"
    category: str = ""
    severity: str = ""
    affected_stage: str = ""
    affected_command: str = ""
    affected_artifact_paths: List[str] = field(default_factory=list)
    release_blocker_status: str = "not_blocker"
    release_blocker_reason: str = "none"
    privacy_redaction_status: str = "none"
    non_training_acknowledgement: bool = False
    status: str = FeedbackEntryStatus.NEW
    developer_notes: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_id": self.feedback_id, "feedback_type": self.feedback_type,
            "timestamp": self.timestamp, "tester_alias": self.tester_alias,
            "category": self.category, "severity": self.severity,
            "affected_stage": self.affected_stage,
            "affected_command": self.affected_command,
            "affected_artifact_paths": list(self.affected_artifact_paths),
            "release_blocker_status": self.release_blocker_status,
            "release_blocker_reason": self.release_blocker_reason,
            "privacy_redaction_status": self.privacy_redaction_status,
            "non_training_acknowledgement": self.non_training_acknowledgement,
            "status": self.status, "developer_notes": self.developer_notes,
            "payload": dict(self.payload),
            "is_training": False, "is_ground_truth": False,
            "modifies_solaris_behavior": False,
        }


@dataclass
class FeedbackLedgerIndex:
    """A regenerable summary view over the ledger."""

    entries: List[FeedbackLedgerEntry] = field(default_factory=list)

    @property
    def release_blocker_count(self) -> int:
        return sum(1 for e in self.entries
                   if e.release_blocker_status in ("release_blocker",
                                                   "stop_testing"))

    @property
    def stop_testing_count(self) -> int:
        return sum(1 for e in self.entries
                   if e.release_blocker_status == "stop_testing")

    @property
    def safety_concern_count(self) -> int:
        return sum(1 for e in self.entries
                   if e.feedback_type == "safety_concern")

    @property
    def redaction_count(self) -> int:
        return sum(1 for e in self.entries
                   if e.privacy_redaction_status == "redacted")

    def by_category(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for e in self.entries:
            key = e.category or e.feedback_type
            out[key] = out.get(key, 0) + 1
        return out

    def by_type(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for e in self.entries:
            out[e.feedback_type] = out.get(e.feedback_type, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_count": len(self.entries),
            "by_type": self.by_type(), "by_category": self.by_category(),
            "release_blocker_count": self.release_blocker_count,
            "stop_testing_count": self.stop_testing_count,
            "safety_concern_count": self.safety_concern_count,
            "redaction_count": self.redaction_count,
            "note": "append-only local QA ledger; feedback is never training, "
                    "ground truth, or a command, and is never deleted",
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        lines = ["# Tester Feedback Index", "",
                 f"- entries: {d['entry_count']}",
                 f"- release blockers: {d['release_blocker_count']} "
                 f"(stop-testing: {d['stop_testing_count']})",
                 f"- safety concerns: {d['safety_concern_count']}",
                 f"- redactions: {d['redaction_count']}",
                 f"- by type: {d['by_type']}", "",
                 "| feedback id | type | category | severity | blocker | status |",
                 "| --- | --- | --- | --- | --- | --- |"]
        for e in self.entries:
            lines.append(
                f"| {e.feedback_id} | {e.feedback_type} | "
                f"{e.category or '-'} | {e.severity or '-'} | "
                f"{e.release_blocker_status} | {e.status} |")
        lines += ["", "_Append-only and local. Feedback is QA evidence only: "
                  "not training, not RLHF, not ground truth, not a command. It "
                  "does not modify Solaris behaviour._"]
        return "\n".join(lines)


@dataclass
class TesterFeedbackLedger:
    """The append-only feedback ledger (JSONL) + regenerable index."""

    ledger_dir: str

    @property
    def jsonl_path(self) -> str:
        return os.path.join(self.ledger_dir, "TESTER_FEEDBACK_LEDGER.jsonl")

    @property
    def json_path(self) -> str:
        return os.path.join(self.ledger_dir, "TESTER_FEEDBACK_LEDGER.json")

    @property
    def index_path(self) -> str:
        return os.path.join(self.ledger_dir, "TESTER_FEEDBACK_INDEX.md")

    def append(self, entry: FeedbackLedgerEntry) -> None:
        os.makedirs(self.ledger_dir, exist_ok=True)
        with open(self.jsonl_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict(), separators=(",", ":")))
            fh.write("\n")

    def load(self) -> FeedbackLedgerIndex:
        index = FeedbackLedgerIndex()
        if not os.path.isfile(self.jsonl_path):
            return index
        with open(self.jsonl_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                index.entries.append(FeedbackLedgerEntry(
                    feedback_id=d.get("feedback_id", ""),
                    feedback_type=d.get("feedback_type", "feedback"),
                    timestamp=d.get("timestamp", ""),
                    tester_alias=d.get("tester_alias", "anonymous"),
                    category=d.get("category", ""),
                    severity=d.get("severity", ""),
                    affected_stage=d.get("affected_stage", ""),
                    affected_command=d.get("affected_command", ""),
                    affected_artifact_paths=list(
                        d.get("affected_artifact_paths", [])),
                    release_blocker_status=d.get("release_blocker_status",
                                                 "not_blocker"),
                    release_blocker_reason=d.get("release_blocker_reason",
                                                 "none"),
                    privacy_redaction_status=d.get("privacy_redaction_status",
                                                   "none"),
                    non_training_acknowledgement=bool(
                        d.get("non_training_acknowledgement", False)),
                    status=d.get("status", FeedbackEntryStatus.NEW),
                    developer_notes=d.get("developer_notes", ""),
                    payload=d.get("payload", {}) or {}))
        return index

    def write_index(self) -> Dict[str, str]:
        index = self.load()
        os.makedirs(self.ledger_dir, exist_ok=True)
        with open(self.json_path, "w", encoding="utf-8") as fh:
            json.dump({**index.to_dict(),
                       "entries": [e.to_dict() for e in index.entries]},
                      fh, indent=2, default=str)
        with open(self.index_path, "w", encoding="utf-8") as fh:
            fh.write(index.to_markdown())
        return {"jsonl": self.jsonl_path, "json": self.json_path,
                "index": self.index_path}
