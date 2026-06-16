"""Evidence continuity ledger -- append-only record of cycle evidence.

:class:`EvidenceContinuityLedger` is the append-only ledger of the evidence
behind a research cycle. Negative, falsified, and missing evidence are all
preserved; entries link back to artifact paths/refs; and stale evidence is marked
superseded, never deleted.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class EvidenceLedgerEntryType:
    BASELINE = "baseline_evidence"
    ROADMAP = "roadmap_evidence"
    ARCHITECTURE_PROPOSAL = "architecture_proposal_evidence"
    COMPILED_EXPERIMENT = "compiled_experiment_evidence"
    IMPLEMENTATION_AUDIT = "implementation_audit_evidence"
    POST_MERGE = "post_merge_evidence"
    VALIDATION = "validation_evidence"
    SOAK = "soak_evidence"
    REPLICATION = "replication_evidence"
    FALSIFICATION = "falsification_evidence"
    SAFETY = "safety_evidence"
    OPERATOR_DECISION = "operator_decision_evidence"
    BLOCKED = "blocked_evidence"
    MISSING = "missing_evidence"
    NEGATIVE = "negative_evidence"
    INCONCLUSIVE = "inconclusive_evidence"

    ALL = (BASELINE, ROADMAP, ARCHITECTURE_PROPOSAL, COMPILED_EXPERIMENT,
           IMPLEMENTATION_AUDIT, POST_MERGE, VALIDATION, SOAK, REPLICATION,
           FALSIFICATION, SAFETY, OPERATOR_DECISION, BLOCKED, MISSING,
           NEGATIVE, INCONCLUSIVE)

    PRESERVED_KINDS = (NEGATIVE, FALSIFICATION, MISSING, BLOCKED, INCONCLUSIVE)


class EvidenceContinuityStatus:
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    PRESERVED = "preserved"

    ALL = (ACTIVE, SUPERSEDED, PRESERVED)


@dataclass
class EvidenceLedgerEntry:
    """One append-only evidence entry (links to an artifact ref/path)."""

    entry_type: str
    summary: str = ""
    artifact_ref: str = ""
    status: str = EvidenceContinuityStatus.ACTIVE
    cycle_id: str = ""
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"entry_type": self.entry_type, "summary": self.summary,
                "artifact_ref": self.artifact_ref, "status": self.status,
                "cycle_id": self.cycle_id, "ts": self.ts}


@dataclass
class EvidenceContinuityLedger:
    """Append-only ledger; negative/falsified/missing evidence is preserved."""

    state_dir: str = ".solaris_ai_nn_research_cycle"
    persist: bool = True
    entries: List[EvidenceLedgerEntry] = field(default_factory=list, init=False)

    @property
    def _ledger_path(self) -> str:
        return os.path.join(self.state_dir, "evidence_ledger.jsonl")

    @property
    def _index_path(self) -> str:
        return os.path.join(self.state_dir, "evidence_index.json")

    def add(self, entry_type: str, *, summary: str = "", artifact_ref: str = "",
            cycle_id: str = "",
            status: str = EvidenceContinuityStatus.ACTIVE,
            ) -> EvidenceLedgerEntry:
        if entry_type not in EvidenceLedgerEntryType.ALL:
            entry_type = EvidenceLedgerEntryType.INCONCLUSIVE
        # Negative/falsified/missing/blocked/inconclusive are preserved.
        if entry_type in EvidenceLedgerEntryType.PRESERVED_KINDS and \
                status == EvidenceContinuityStatus.ACTIVE:
            status = EvidenceContinuityStatus.PRESERVED
        entry = EvidenceLedgerEntry(entry_type=entry_type, summary=summary,
                                    artifact_ref=artifact_ref, cycle_id=cycle_id,
                                    status=status)
        self.entries.append(entry)
        if self.persist:
            self._append(entry)
        return entry

    def supersede(self, entry_type: str) -> int:
        """Mark prior active entries of a type superseded (never deleted)."""
        count = 0
        for e in self.entries:
            if e.entry_type == entry_type and \
                    e.status == EvidenceContinuityStatus.ACTIVE:
                e.status = EvidenceContinuityStatus.SUPERSEDED
                count += 1
        if count and self.persist:
            self._write_index()
        return count

    def _append(self, entry: EvidenceLedgerEntry) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._ledger_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.to_dict(), default=str) + "\n")
        self._write_index()

    def _write_index(self) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._index_path, "w", encoding="utf-8") as fh:
            json.dump(self.index(), fh, indent=2, default=str)

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for e in self.entries:
            out[e.entry_type] = out.get(e.entry_type, 0) + 1
        return out

    @property
    def negative_count(self) -> int:
        return sum(1 for e in self.entries
                   if e.entry_type == EvidenceLedgerEntryType.NEGATIVE)

    @property
    def falsified_count(self) -> int:
        return sum(1 for e in self.entries
                   if e.entry_type == EvidenceLedgerEntryType.FALSIFICATION)

    @property
    def missing_count(self) -> int:
        return sum(1 for e in self.entries
                   if e.entry_type == EvidenceLedgerEntryType.MISSING)

    def index(self) -> Dict[str, Any]:
        return {
            "evidence_ledger_entry_count": len(self.entries),
            "counts": self.counts(),
            "negative_evidence_entry_count": self.negative_count,
            "falsified_evidence_entry_count": self.falsified_count,
            "missing_evidence_entry_count": self.missing_count,
            "superseded_count": sum(
                1 for e in self.entries
                if e.status == EvidenceContinuityStatus.SUPERSEDED),
            "append_only": True,
        }

    def to_dict(self) -> Dict[str, Any]:
        d = self.index()
        d["entries"] = [e.to_dict() for e in self.entries]
        d["note"] = ("append-only; negative/falsified/missing evidence is "
                     "preserved, and stale evidence is marked superseded, never "
                     "deleted")
        return d
