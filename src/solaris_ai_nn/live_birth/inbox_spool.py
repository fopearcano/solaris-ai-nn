"""Live inbox spool -- bounded read of local JSONL event files.

:class:`LiveInboxSpool` lists JSONL files from the inbox, reads a bounded number of
events, validates each, routes invalid/unsafe events to quarantine, and indexes
accepted events. Reads are bounded: it does not tail forever, watch the filesystem
indefinitely, delete inbox files, follow links, open remote URLs, or execute
anything from event contents.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .event_schema import LiveEventEnvelope
from .event_validator import LiveEventValidationResult, LiveEventValidator
from .quarantine import QuarantineReason, QuarantineStore


@dataclass
class InboxBatch:
    """One bounded batch of read events + their validation results."""

    envelopes: List[LiveEventEnvelope] = field(default_factory=list)
    results: List[LiveEventValidationResult] = field(default_factory=list)

    def accepted(self) -> List[LiveEventEnvelope]:
        return [e for e, r in zip(self.envelopes, self.results) if r.accepted]


@dataclass
class InboxReadResult:
    """Aggregate result of a bounded inbox read."""

    files_read: List[str] = field(default_factory=list)
    event_count: int = 0
    accepted_count: int = 0
    quarantined_count: int = 0
    truncated: bool = False
    accepted_envelopes: List[LiveEventEnvelope] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "live_inbox_file_count": len(self.files_read),
            "files_read": [os.path.basename(f) for f in self.files_read],
            "live_event_count": self.event_count,
            "live_event_accepted_count": self.accepted_count,
            "live_event_quarantined_count": self.quarantined_count,
            "truncated": self.truncated,
            "note": "bounded read of local JSONL files only; no tailing, "
                    "watching, deletion, link-following, or remote access",
        }


@dataclass
class LiveInboxSpool:
    """Reads a bounded batch of events from the local inbox directory."""

    inbox_dir: str
    validator: LiveEventValidator
    quarantine: QuarantineStore
    max_files: int = 50
    max_events: int = 500
    max_bytes: int = 5_000_000
    strict: bool = False

    def list_files(self) -> List[str]:
        if not os.path.isdir(self.inbox_dir):
            return []
        out: List[str] = []
        for name in sorted(os.listdir(self.inbox_dir)):
            path = os.path.join(self.inbox_dir, name)
            # Bounded, local, regular .jsonl files only; never follow links.
            if os.path.islink(path):
                continue
            if not os.path.isfile(path):
                continue
            if not name.endswith(".jsonl"):
                continue
            out.append(path)
            if len(out) >= self.max_files:
                break
        return out

    def read(self) -> InboxReadResult:
        result = InboxReadResult()
        bytes_read = 0
        for path in self.list_files():
            result.files_read.append(path)
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
            if bytes_read + size > self.max_bytes:
                result.truncated = True
                break
            bytes_read += size
            stop = self._read_file(path, result)
            if stop:
                result.truncated = True
                break
        return result

    def _read_file(self, path: str, result: InboxReadResult) -> bool:
        """Read one JSONL file; returns True if the event budget is exhausted."""
        with open(path, "r", encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                if result.event_count >= self.max_events:
                    return True
                result.event_count += 1
                try:
                    raw = json.loads(line)
                except Exception:
                    raw = {"_invalid_json": line[:200]}
                envelope = LiveEventEnvelope(raw=raw, source_file=path,
                                             line_number=line_number)
                if not isinstance(raw, dict):
                    self.quarantine.add(
                        QuarantineReason.INVALID_JSON, source_file=path,
                        line_number=line_number, original=line[:200],
                        detail="invalid JSON line")
                    result.quarantined_count += 1
                    continue
                validation = self.validator.validate(envelope)
                if validation.accepted:
                    result.accepted_count += 1
                    result.accepted_envelopes.append(envelope)
                else:
                    self.quarantine.add(
                        validation.quarantine_reason or QuarantineReason.UNKNOWN,
                        source_file=path, line_number=line_number,
                        original=raw, event_id=str(raw.get("event_id", "")),
                        detail="; ".join(f.detail for f in validation.findings
                                         if f.detail))
                    result.quarantined_count += 1
        return False
