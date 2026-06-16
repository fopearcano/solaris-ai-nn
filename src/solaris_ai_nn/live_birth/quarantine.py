"""Quarantine -- preserve unsafe/invalid events as evidence, never delete.

:class:`QuarantineStore` records invalid or unsafe events with their reason and
source file. Quarantine preserves the original event content, is evidence (not
deletion), and quarantined events never enter the sensory membrane.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class QuarantineReason:
    INVALID_JSON = "invalid_json"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    SOURCE_NOT_REGISTERED = "source_not_registered"
    SOURCE_FORBIDDEN = "source_forbidden"
    GOVERNANCE_BLOCKED = "governance_blocked"
    READ_ONLY_FALSE = "read_only_false"
    IS_COMMAND_TRUE = "is_command_true"
    HUMAN_LABEL_GROUND_TRUTH_TRUE = "human_label_ground_truth_true"
    DEBUG_GLOSS_GROUND_TRUTH_TRUE = "debug_gloss_ground_truth_true"
    CONTAINS_SECRET = "contains_secret"
    CONTAINS_INSTRUCTION = "contains_instruction"
    PRIVATE_DATA = "private_data"
    RAW_STREAM = "raw_stream"
    OVERSIZED_PAYLOAD = "oversized_payload"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    UNKNOWN = "unknown"

    ALL = (INVALID_JSON, MISSING_REQUIRED_FIELD, SOURCE_NOT_REGISTERED,
           SOURCE_FORBIDDEN, GOVERNANCE_BLOCKED, READ_ONLY_FALSE,
           IS_COMMAND_TRUE, HUMAN_LABEL_GROUND_TRUTH_TRUE,
           DEBUG_GLOSS_GROUND_TRUTH_TRUE, CONTAINS_SECRET, CONTAINS_INSTRUCTION,
           PRIVATE_DATA, RAW_STREAM, OVERSIZED_PAYLOAD, UNSUPPORTED_CLAIM,
           UNKNOWN)


@dataclass
class QuarantineRecord:
    """One quarantined event (original preserved)."""

    reason: str
    source_file: str
    line_number: int
    original: Any
    event_id: str = ""
    detail: str = ""
    ts: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.reason not in QuarantineReason.ALL:
            self.reason = QuarantineReason.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return {"reason": self.reason, "source_file": self.source_file,
                "line_number": self.line_number, "event_id": self.event_id,
                "detail": self.detail, "original": self.original, "ts": self.ts,
                "entered_membrane": False}


@dataclass
class QuarantineStore:
    """Append-only quarantine store; preserves originals, never deletes."""

    state_dir: str = ".solaris_ai_nn_live"
    records: List[QuarantineRecord] = field(default_factory=list)

    @property
    def _dir(self) -> str:
        return os.path.join(self.state_dir, "quarantine")

    @property
    def index_path(self) -> str:
        return os.path.join(self._dir, "QUARANTINE_INDEX.json")

    @property
    def report_path(self) -> str:
        return os.path.join(self._dir, "QUARANTINE_REPORT.md")

    def add(self, reason: str, *, source_file: str, line_number: int,
            original: Any, event_id: str = "", detail: str = "",
            ) -> QuarantineRecord:
        rec = QuarantineRecord(reason=reason, source_file=source_file,
                               line_number=line_number, original=original,
                               event_id=event_id, detail=detail)
        self.records.append(rec)
        return rec

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for r in self.records:
            out[r.reason] = out.get(r.reason, 0) + 1
        return out

    def index(self) -> Dict[str, Any]:
        return {
            "quarantined_event_count": len(self.records),
            "reasons": self.counts(),
            "note": "quarantine preserves the original event and reason; it is "
                    "evidence, not deletion, and quarantined events never enter "
                    "the sensory membrane",
        }

    def to_dict(self) -> Dict[str, Any]:
        d = self.index()
        d["records"] = [r.to_dict() for r in self.records]
        return d

    def write(self) -> Dict[str, str]:
        os.makedirs(self._dir, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)
        with open(self.report_path, "w", encoding="utf-8") as fh:
            fh.write(self._render_md())
        return {"index": self.index_path, "report": self.report_path}

    def _render_md(self) -> str:
        lines = ["# Live Birth Quarantine Report", "",
                 f"- quarantined events: {len(self.records)}", "",
                 "| reason | event id | source file:line | detail |",
                 "| --- | --- | --- | --- |"]
        for r in self.records:
            lines.append(f"| {r.reason} | {r.event_id} | "
                         f"{os.path.basename(r.source_file)}:{r.line_number} | "
                         f"{r.detail} |")
        lines += ["", "_Quarantine preserves the original event and reason; it is "
                  "evidence, not deletion. Quarantined events never enter the "
                  "sensory membrane._"]
        return "\n".join(lines) + "\n"
