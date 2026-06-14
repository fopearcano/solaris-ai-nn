"""Sensory provenance -- every environmental event carries its origin.

The :class:`ProvenanceLedger` records, for each sensory event, where it came
from (source id/type, path hash, raw line hash, adapter), whether the source
was read-only-validated, whether it is simulated or real, its trust level, and
the limitations of the reading. Provenance is mandatory: an event without
provenance is not admissible as evidence.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(
        str(text).encode("utf-8", "replace")).hexdigest()[:32]


@dataclass
class ProvenanceRecord:
    """The origin record for one sensory event."""

    event_hash: str
    source_id: str
    source_type: str
    adapter_name: str
    path_hash: Optional[str] = None
    raw_line_hash: Optional[str] = None
    read_only_validated: bool = False
    is_simulated: bool = False
    trust_level: str = "low"
    limitations: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ProvenanceLedger:
    """Append-only ledger of sensory provenance records."""

    state_dir: Optional[str] = None
    records: List[ProvenanceRecord] = field(default_factory=list, init=False)
    write_log: bool = True

    def __post_init__(self) -> None:
        self.path = (os.path.join(self.state_dir, "sensory_provenance.jsonl")
                     if self.state_dir else None)

    def record(self, record: ProvenanceRecord) -> ProvenanceRecord:
        self.records.append(record)
        self.records = self.records[-5000:]
        if self.write_log and self.path is not None:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record.to_dict(), default=str) + "\n")
        return record

    def record_for(self, *, event_hash: str, source_id: str, source_type: str,
                   adapter_name: str, path: Optional[str] = None,
                   raw_line: Optional[str] = None,
                   read_only_validated: bool = False,
                   is_simulated: bool = False, trust_level: str = "low",
                   limitations: Optional[List[str]] = None,
                   ) -> ProvenanceRecord:
        return self.record(ProvenanceRecord(
            event_hash=event_hash, source_id=source_id,
            source_type=source_type, adapter_name=adapter_name,
            path_hash=hash_text(path) if path else None,
            raw_line_hash=hash_text(raw_line) if raw_line is not None else None,
            read_only_validated=read_only_validated, is_simulated=is_simulated,
            trust_level=trust_level, limitations=list(limitations or [])))

    def completeness(self, event_count: int) -> float:
        """Fraction of events that carry a provenance record."""
        if event_count <= 0:
            return 1.0 if not self.records else 1.0
        return round(min(1.0, len(self.records) / event_count), 4)

    def snapshot(self) -> Dict[str, Any]:
        by_source: Dict[str, int] = {}
        simulated = 0
        for r in self.records:
            by_source[r.source_id] = by_source.get(r.source_id, 0) + 1
            simulated += int(r.is_simulated)
        return {
            "record_count": len(self.records),
            "by_source": by_source,
            "simulated_count": simulated,
            "real_count": len(self.records) - simulated,
            "path": self.path,
        }
