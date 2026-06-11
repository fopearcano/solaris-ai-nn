"""Communication transcript -- every exchange on the record, sanitized.

Each entry records the operator, sanitized input, classification, command
id, response summary, and the safety/governance decisions, persisted as
JSONL. No secrets, no large payloads: inputs are truncated, token-shaped
fragments are masked, and unsafe input is stored as a sanitized summary.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

MAX_STORED_INPUT = 200
_SECRET_RE = re.compile(
    r"(?i)\b(token|secret|password|api[_-]?key|bearer)\b\s*[:=]?\s*\S+")


def sanitize_text(text: str, limit: int = MAX_STORED_INPUT) -> str:
    """Mask secret-shaped fragments, drop control chars, truncate."""
    cleaned = "".join(ch for ch in str(text) if ch.isprintable())
    cleaned = _SECRET_RE.sub(lambda m: f"{m.group(1)}=[redacted]", cleaned)
    if len(cleaned) > limit:
        cleaned = cleaned[:limit] + "...[truncated]"
    return cleaned


@dataclass
class TranscriptEntry:
    """One exchange: input, decisions, and the response summary."""

    operator: str = ""
    raw_input: str = ""  # sanitized before storage
    classification: str = "unknown"
    command_id: str = ""
    response_summary: str = ""
    safety_decision: str = ""
    governance_decision: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class CommunicationTranscript:
    """Bounded in memory, append-only on disk."""

    state_dir: Optional[Union[str, Path]] = None
    max_entries: int = 500
    entries: List[TranscriptEntry] = field(default_factory=list,
                                           init=False)
    rows_written: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.path = (Path(self.state_dir) / "operator_transcript.jsonl"
                     if self.state_dir else None)

    def record(self, operator: str, raw_input: str, classification: str,
               response_summary: str = "", command_id: str = "",
               safety_decision: str = "", governance_decision: str = "",
               evidence_refs: Optional[List[str]] = None,
               unsafe: bool = False,
               metadata: Optional[Dict[str, Any]] = None,
               ) -> TranscriptEntry:
        stored_input = sanitize_text(raw_input)
        if unsafe:
            stored_input = (f"[unsafe input; sanitized summary] "
                            f"{stored_input[:80]}")
        entry = TranscriptEntry(
            operator=operator, raw_input=stored_input,
            classification=classification, command_id=command_id,
            response_summary=sanitize_text(response_summary, 240),
            safety_decision=safety_decision,
            governance_decision=governance_decision,
            evidence_refs=list(evidence_refs or [])[:10],
            metadata=dict(metadata or {}))
        self.entries.append(entry)
        self.entries = self.entries[-self.max_entries:]
        self._write(entry)
        return entry

    def _write(self, entry: TranscriptEntry) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict(), default=str) + "\n")
        self.rows_written += 1

    # -- views --------------------------------------------------------------------

    def tail(self, limit: int = 10) -> List[TranscriptEntry]:
        return self.entries[-limit:]

    def summary(self) -> Dict[str, Any]:
        kinds: Dict[str, int] = {}
        for entry in self.entries:
            kinds[entry.classification] = kinds.get(
                entry.classification, 0) + 1
        return {
            "entries_in_memory": len(self.entries),
            "rows_written": self.rows_written,
            "path": str(self.path) if self.path else None,
            "by_classification": kinds,
        }

    def snapshot(self) -> Dict[str, Any]:
        return {**self.summary(),
                "recent": [e.to_dict() for e in self.entries[-5:]]}
