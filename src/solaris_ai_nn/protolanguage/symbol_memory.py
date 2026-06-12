"""Symbol memory -- the life and death of every sign, on the record.

Births, reinforcements, decay, merges, ambiguity, extinction,
fossilization, rule emergence, and rule failure persist as JSONL across
long runs, so that after months the question "which symbols survived,
and why?" has an auditable answer.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

SYMBOL_EVENTS = ("birth", "reinforcement", "decay", "merge",
                 "ambiguity", "extinction", "fossilization",
                 "rule_emergence", "rule_failure")


@dataclass
class SymbolMemoryRecord:
    """One lifecycle event for one sign (or one rule)."""

    event: str
    token: str = ""
    symbol_id: str = ""
    detail: str = ""
    lifetime_s: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if self.event not in SYMBOL_EVENTS:
            raise ValueError(f"unknown symbol event {self.event!r}")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SymbolMemory:
    """Bounded in memory, append-only JSONL on disk."""

    state_dir: Optional[Union[str, Path]] = None
    max_records: int = 1000
    records: List[SymbolMemoryRecord] = field(default_factory=list,
                                              init=False)
    rows_written: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        base = Path(self.state_dir) if self.state_dir else None
        self.memory_path = (base / "symbol_memory.jsonl"
                            if base else None)
        self.rules_path = base / "symbol_rules.json" if base else None
        self.sequences_path = (base / "symbol_sequences.jsonl"
                               if base else None)

    def record(self, event: str, token: str = "", symbol_id: str = "",
               detail: str = "",
               lifetime_s: float = 0.0) -> SymbolMemoryRecord:
        entry = SymbolMemoryRecord(event=event, token=token,
                                   symbol_id=symbol_id, detail=detail,
                                   lifetime_s=lifetime_s)
        self.records.append(entry)
        self.records = self.records[-self.max_records:]
        if self.memory_path is not None:
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry.to_dict(), default=str)
                         + "\n")
            self.rows_written += 1
        return entry

    def save_rules(self, rules: List[Any]) -> Optional[str]:
        if self.rules_path is None:
            return None
        self.rules_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.rules_path, "w", encoding="utf-8") as fh:
            json.dump([r.to_dict() if hasattr(r, "to_dict") else r
                       for r in rules], fh, indent=2, default=str)
        return str(self.rules_path)

    def record_sequence(self, sequence: Any) -> None:
        if self.sequences_path is None:
            return
        self.sequences_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.sequences_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(
                sequence.to_dict() if hasattr(sequence, "to_dict")
                else sequence, default=str) + "\n")

    # -- views --------------------------------------------------------------------

    def counts_by_event(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for record in self.records:
            counts[record.event] = counts.get(record.event, 0) + 1
        return counts

    def snapshot(self) -> Dict[str, Any]:
        return {
            "records_in_memory": len(self.records),
            "rows_written": self.rows_written,
            "counts_by_event": self.counts_by_event(),
            "memory_path": (str(self.memory_path)
                            if self.memory_path else None),
            "rules_path": (str(self.rules_path)
                           if self.rules_path else None),
            "recent": [r.to_dict() for r in self.records[-5:]],
        }
