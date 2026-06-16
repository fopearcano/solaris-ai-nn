"""Research cycle archive -- local metadata; archived cycles stay visible.

:class:`ResearchCycleArchive` records archived cycles with a reason. The archive
is local metadata: archived cycles remain visible, archiving deletes no artifacts,
and an archived cycle can be used as future evidence.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


class ArchiveReason:
    COMPLETED = "completed"
    SUPERSEDED = "superseded"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    BLOCKED_BY_MISSING_EVIDENCE = "blocked_by_missing_evidence"
    BLOCKED_BY_FALSIFICATION = "blocked_by_falsification"
    OPERATOR_ABANDONED = "operator_abandoned"
    INCONCLUSIVE = "inconclusive"
    UNKNOWN = "unknown"

    ALL = (COMPLETED, SUPERSEDED, BLOCKED_BY_SAFETY,
           BLOCKED_BY_MISSING_EVIDENCE, BLOCKED_BY_FALSIFICATION,
           OPERATOR_ABANDONED, INCONCLUSIVE, UNKNOWN)


@dataclass
class ArchivedCycleRecord:
    """One archived cycle (local metadata; artifacts are not deleted)."""

    cycle_id: str
    reason: str
    final_stage: str = ""
    detail: str = ""
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"cycle_id": self.cycle_id, "reason": self.reason,
                "final_stage": self.final_stage, "detail": self.detail,
                "ts": self.ts, "artifacts_deleted": False, "visible": True}


@dataclass
class ResearchCycleArchive:
    """Holds archived cycle records (visible; deletes nothing)."""

    records: List[ArchivedCycleRecord] = field(default_factory=list)

    def archive(self, cycle_id: str, reason: str, *, final_stage: str = "",
                detail: str = "") -> ArchivedCycleRecord:
        if reason not in ArchiveReason.ALL:
            reason = ArchiveReason.UNKNOWN
        rec = ArchivedCycleRecord(cycle_id=cycle_id, reason=reason,
                                  final_stage=final_stage, detail=detail)
        self.records.append(rec)
        return rec

    def to_dict(self) -> Dict[str, Any]:
        return {
            "archived_cycle_count": len(self.records),
            "records": [r.to_dict() for r in self.records],
            "note": "archive is local metadata; archived cycles remain visible, "
                    "no artifacts are deleted, and an archived cycle can be used "
                    "as future evidence",
        }
