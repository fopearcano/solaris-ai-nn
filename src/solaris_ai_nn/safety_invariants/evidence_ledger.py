"""Safety evidence ledger -- append-only; critical failures cannot be hidden.

The :class:`SafetyEvidenceLedger` records invariant checks, red-team results,
boundary regressions, firewall audits, ClaimGuard scans, governance blocks,
emergency-stop tests, non-actuation proofs, missing-evidence warnings, and
unresolved safety issues. It is append-only and feeds the assurance case. A
critical failure is always visible.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SafetyEvidenceKind:
    INVARIANT_CHECK = "invariant_check"
    RED_TEAM_RESULT = "red_team_result"
    BOUNDARY_REGRESSION = "boundary_regression"
    FIREWALL_AUDIT = "firewall_audit"
    CLAIM_GUARD_SCAN = "claim_guard_scan"
    GOVERNANCE_BLOCK = "governance_block"
    EMERGENCY_STOP_TEST = "emergency_stop_test"
    NON_ACTUATION_PROOF = "non_actuation_proof"
    MISSING_EVIDENCE_WARNING = "missing_evidence_warning"
    UNRESOLVED_SAFETY_ISSUE = "unresolved_safety_issue"

    ALL = (INVARIANT_CHECK, RED_TEAM_RESULT, BOUNDARY_REGRESSION,
           FIREWALL_AUDIT, CLAIM_GUARD_SCAN, GOVERNANCE_BLOCK,
           EMERGENCY_STOP_TEST, NON_ACTUATION_PROOF, MISSING_EVIDENCE_WARNING,
           UNRESOLVED_SAFETY_ISSUE)


@dataclass
class SafetyEvidenceRecord:
    """One append-only safety evidence record."""

    kind: str
    summary: str
    passed: Optional[bool] = None
    critical: bool = False
    detail: Dict[str, Any] = field(default_factory=dict)
    evidence_refs: List[str] = field(default_factory=list)
    record_id: str = field(
        default_factory=lambda: f"SEV_{uuid.uuid4().hex[:10]}")
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SafetyEvidenceLedger:
    """Append-only ledger of safety evidence; feeds the assurance case."""

    state_dir: Optional[str] = None
    write_log: bool = True
    records: List[SafetyEvidenceRecord] = field(default_factory=list,
                                                init=False)
    write_failures: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self._invariant_path = self._p("safety_invariant_results.jsonl")
        self._red_team_path = self._p("red_team_results.jsonl")
        self._ledger_path = self._p("safety_evidence_ledger.jsonl")

    def _p(self, name: str) -> Optional[str]:
        return os.path.join(self.state_dir, name) if self.state_dir else None

    def _append(self, path: Optional[str], obj: Dict[str, Any]) -> None:
        if not (self.write_log and path):
            return
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(obj, default=str) + "\n")
        except OSError:
            self.write_failures += 1

    def record(self, record: SafetyEvidenceRecord) -> SafetyEvidenceRecord:
        self.records.append(record)
        self._append(self._ledger_path, record.to_dict())
        if record.kind == SafetyEvidenceKind.INVARIANT_CHECK:
            self._append(self._invariant_path, record.to_dict())
        elif record.kind == SafetyEvidenceKind.RED_TEAM_RESULT:
            self._append(self._red_team_path, record.to_dict())
        return record

    # -- typed helpers ----------------------------------------------------------

    def record_invariant_bundle(self, bundle: Any) -> None:
        for r in getattr(bundle, "results", []):
            self.record(SafetyEvidenceRecord(
                kind=SafetyEvidenceKind.INVARIANT_CHECK,
                summary=f"{r.category}:{r.status}", passed=r.passed,
                critical=r.is_escalating_failure, detail=r.to_dict(),
                evidence_refs=list(r.evidence_refs)))

    def record_red_team(self, results: List[Any]) -> None:
        for r in results:
            self.record(SafetyEvidenceRecord(
                kind=SafetyEvidenceKind.RED_TEAM_RESULT,
                summary=f"{r.scenario_type}:{'blocked' if r.blocked else 'ACCEPTED'}",
                passed=r.blocked, critical=r.critical, detail=r.to_dict(),
                evidence_refs=list(r.evidence_refs)))

    def record_boundary(self, results: List[Any]) -> None:
        for r in results:
            self.record(SafetyEvidenceRecord(
                kind=SafetyEvidenceKind.BOUNDARY_REGRESSION,
                summary=f"{r.boundary}:{r.status}", passed=r.passed,
                critical=r.boundary_crossed, detail=r.to_dict(),
                evidence_refs=list(r.evidence_refs)))

    def record_missing_evidence(self, what: str) -> None:
        self.record(SafetyEvidenceRecord(
            kind=SafetyEvidenceKind.MISSING_EVIDENCE_WARNING,
            summary=f"missing evidence: {what}", passed=False, critical=False))

    # -- queries ----------------------------------------------------------------

    def critical_records(self) -> List[SafetyEvidenceRecord]:
        return [r for r in self.records if r.critical]

    def unresolved_issues(self) -> List[SafetyEvidenceRecord]:
        return [r for r in self.records
                if r.critical or (r.passed is False
                                  and r.kind != SafetyEvidenceKind.
                                  MISSING_EVIDENCE_WARNING)]

    def completeness_score(self) -> float:
        """Fraction of records that carry evidence refs (proxy completeness)."""
        if not self.records:
            return 0.0
        with_refs = sum(1 for r in self.records if r.evidence_refs)
        return round(with_refs / len(self.records), 4)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "record_count": len(self.records),
            "critical_count": len(self.critical_records()),
            "unresolved_count": len(self.unresolved_issues()),
            "completeness_score": self.completeness_score(),
            "write_failures": self.write_failures,
            "ledger_path": self._ledger_path,
            "recent": [r.to_dict() for r in self.records[-8:]],
        }
