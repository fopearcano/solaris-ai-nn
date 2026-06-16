"""Implementation coverage matrix -- make gaps obvious (no empty green board).

:class:`ImplementationCoverageMatrix` joins each spec requirement to its
implemented-file / test / example / docs / report / safety evidence and a
status. The matrix is built so gaps are visible: unknown/missing evidence stays
on the board, and there is no all-green dashboard when evidence is absent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class CoverageStatus:
    COVERED = "covered"
    PARTIAL = "partial"
    GAP = "gap"
    UNKNOWN = "unknown"
    BLOCKED = "blocked"

    ALL = (COVERED, PARTIAL, GAP, UNKNOWN, BLOCKED)


@dataclass
class CoverageMatrixRow:
    """One spec requirement and its multi-kind evidence + status."""

    requirement: str
    expected_file: str = ""
    implemented_file_evidence: List[str] = field(default_factory=list)
    test_evidence: bool = False
    example_evidence: bool = False
    docs_evidence: bool = False
    report_evidence: bool = False
    safety_evidence: bool = False
    status: str = CoverageStatus.UNKNOWN
    blocker: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirement": self.requirement,
            "expected_file": self.expected_file,
            "implemented_file_evidence": list(self.implemented_file_evidence),
            "test_evidence": self.test_evidence,
            "example_evidence": self.example_evidence,
            "docs_evidence": self.docs_evidence,
            "report_evidence": self.report_evidence,
            "safety_evidence": self.safety_evidence,
            "status": self.status, "blocker": self.blocker, "notes": self.notes}


@dataclass
class ImplementationCoverageMatrix:
    """A conservative coverage grid; gaps stay visible."""

    rows: List[CoverageMatrixRow] = field(default_factory=list)

    def add(self, row: CoverageMatrixRow) -> None:
        self.rows.append(row)

    def counts(self) -> Dict[str, int]:
        out = {s: 0 for s in CoverageStatus.ALL}
        for r in self.rows:
            out[r.status] = out.get(r.status, 0) + 1
        return out

    @property
    def gap_count(self) -> int:
        c = self.counts()
        return c[CoverageStatus.GAP] + c[CoverageStatus.UNKNOWN] + \
            c[CoverageStatus.BLOCKED]

    @property
    def empty_green_dashboard(self) -> bool:
        # An all-green board with no evidence rows would be a false dashboard.
        return bool(self.rows) and self.gap_count == 0 and all(
            not (r.test_evidence or r.implemented_file_evidence)
            for r in self.rows)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row_count": len(self.rows),
            "rows": [r.to_dict() for r in self.rows],
            "counts": self.counts(),
            "coverage_gap_count": self.gap_count,
            "blocker_count": sum(1 for r in self.rows if r.blocker),
            "empty_green_dashboard": self.empty_green_dashboard,
            "note": "gaps stay visible; unknown/missing evidence is not hidden "
                    "and there is no empty green dashboard",
        }


_STATUS_MAP = {
    "satisfied": CoverageStatus.COVERED,
    "partially_satisfied": CoverageStatus.PARTIAL,
    "not_satisfied": CoverageStatus.GAP,
    "blocked": CoverageStatus.BLOCKED,
    "not_applicable": CoverageStatus.COVERED,
    "unknown": CoverageStatus.UNKNOWN,
}


def build_coverage_matrix(*, spec_compliance: Optional[Dict] = None,
                          diff_audit: Optional[Dict] = None,
                          test_audit: Optional[Dict] = None,
                          ) -> ImplementationCoverageMatrix:
    """Build the coverage matrix from the other audits' results."""
    spec_compliance = spec_compliance or {}
    diff_audit = diff_audit or {}
    test_audit = test_audit or {}
    matrix = ImplementationCoverageMatrix()

    # Which evidence kinds are present overall (from the diff assessments)?
    categories = {a["category"] for a in diff_audit.get("assessments", [])}
    docs_present = "docs" in categories
    example_present = "example" in categories
    report_present = "report" in categories
    safety_records = test_audit.get("records", [])
    safety_present = any(r["category"] == "safety" and r["present"]
                         for r in safety_records)
    tests_green = test_audit.get("passes", None)

    items = spec_compliance.get("items", [])
    if not items:
        matrix.add(CoverageMatrixRow(
            requirement="no spec requirements supplied",
            status=CoverageStatus.UNKNOWN,
            notes="no compiled spec to measure coverage against"))
        return matrix

    for item in items:
        status = _STATUS_MAP.get(item["status"], CoverageStatus.UNKNOWN)
        evidence = list(item.get("evidence", []))
        is_test = item["category"] == "test"
        is_safety = item["category"] == "safety_gate"
        blocker = bool(item.get("blocking")) and status in (
            CoverageStatus.GAP, CoverageStatus.BLOCKED, CoverageStatus.UNKNOWN)
        matrix.add(CoverageMatrixRow(
            requirement=item["requirement"],
            expected_file=evidence[0] if evidence else "",
            implemented_file_evidence=evidence,
            test_evidence=is_test and bool(tests_green),
            example_evidence=item["category"] == "example" and example_present,
            docs_evidence=item["category"] == "docs" and docs_present,
            report_evidence=report_present,
            safety_evidence=is_safety and safety_present,
            status=status, blocker=blocker,
            notes=item.get("note", "")))
    return matrix
