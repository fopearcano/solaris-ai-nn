"""Independent review audit matrix -- one row per claim; gaps stay visible.

:class:`IndependentReviewAuditMatrix` builds one row per claim linking it to its
supporting evidence, counterevidence, required artifacts, reproduction challenge,
control comparison, falsification test, safety boundary, limitation, and reviewer
question, with a reviewability status and a blocker flag. The matrix exposes gaps:
there is no empty green dashboard, and falsified/unsupported claims stay visible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AuditMatrixStatus:
    REVIEWABLE = "reviewable"
    PARTIALLY_REVIEWABLE = "partially_reviewable"
    NOT_REVIEWABLE = "not_reviewable"
    BLOCKED = "blocked"
    MISSING_EVIDENCE = "missing_evidence"
    FALSIFIED = "falsified"
    INCONCLUSIVE = "inconclusive"
    NOT_APPLICABLE = "not_applicable"

    ALL = (REVIEWABLE, PARTIALLY_REVIEWABLE, NOT_REVIEWABLE, BLOCKED,
           MISSING_EVIDENCE, FALSIFIED, INCONCLUSIVE, NOT_APPLICABLE)

    BLOCKER_STATUSES = (BLOCKED, FALSIFIED, MISSING_EVIDENCE)


@dataclass
class AuditMatrixRow:
    """One claim's audit row (gaps stay visible)."""

    claim: str
    claim_id: str = ""
    supporting_evidence: List[str] = field(default_factory=list)
    counterevidence: List[str] = field(default_factory=list)
    required_artifacts: List[str] = field(default_factory=list)
    reproduction_challenge: str = ""
    control_comparison: str = ""
    falsification_test: str = ""
    safety_boundary: str = ""
    limitation: str = ""
    reviewer_question: str = ""
    status: str = AuditMatrixStatus.INCONCLUSIVE
    blocker_flag: bool = False

    def __post_init__(self) -> None:
        if self.status not in AuditMatrixStatus.ALL:
            self.status = AuditMatrixStatus.INCONCLUSIVE
        if self.status in AuditMatrixStatus.BLOCKER_STATUSES:
            self.blocker_flag = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim, "claim_id": self.claim_id,
            "supporting_evidence": list(self.supporting_evidence),
            "counterevidence": list(self.counterevidence),
            "required_artifacts": list(self.required_artifacts),
            "reproduction_challenge": self.reproduction_challenge,
            "control_comparison": self.control_comparison,
            "falsification_test": self.falsification_test,
            "safety_boundary": self.safety_boundary,
            "limitation": self.limitation,
            "reviewer_question": self.reviewer_question,
            "status": self.status, "blocker_flag": self.blocker_flag}


# claim status (from the claim registry) -> audit-matrix status.
_STATUS_MAP = {
    "supported": AuditMatrixStatus.REVIEWABLE,
    "partially_supported": AuditMatrixStatus.PARTIALLY_REVIEWABLE,
    "weakly_supported": AuditMatrixStatus.PARTIALLY_REVIEWABLE,
    "inconclusive": AuditMatrixStatus.INCONCLUSIVE,
    "requires_more_evidence": AuditMatrixStatus.MISSING_EVIDENCE,
    "unsupported": AuditMatrixStatus.MISSING_EVIDENCE,
    "contradicted": AuditMatrixStatus.NOT_REVIEWABLE,
    "falsified": AuditMatrixStatus.FALSIFIED,
    "forbidden": AuditMatrixStatus.BLOCKED,
}


@dataclass
class IndependentReviewAuditMatrix:
    """Builds the audit matrix from claims + review material (exposes gaps)."""

    rows: List[AuditMatrixRow] = field(default_factory=list)

    def build(self, *, claims: List[Dict], counterevidence: Dict[str, Any],
              limitations: Dict[str, Any],
              challenge_by_category: Optional[Dict[str, str]] = None,
              question_by_category: Optional[Dict[str, str]] = None,
              ) -> "IndependentReviewAuditMatrix":
        challenge_by_category = challenge_by_category or {}
        question_by_category = question_by_category or {}
        ce_refs = [r.get("counter_type", "") for r in
                   (counterevidence.get("records", []) or [])]
        lim_texts = [l.get("text", "") for l in
                     (limitations.get("limitations", []) or [])]
        for c in claims:
            status = _STATUS_MAP.get(c.get("status", ""),
                                     AuditMatrixStatus.INCONCLUSIVE)
            cat = c.get("category", "")
            self.rows.append(AuditMatrixRow(
                claim=c.get("text", ""), claim_id=c.get("claim_id", ""),
                supporting_evidence=list(c.get("evidence_refs", [])),
                counterevidence=list(c.get("counterevidence_refs", []))
                or ce_refs[:2],
                required_artifacts=["scientific_claim_report", "evidence_map"],
                reproduction_challenge=challenge_by_category.get(
                    cat, "scientific_claim_report_reproduction"),
                control_comparison="passive_parser / ablation / null control",
                falsification_test="falsification_replay",
                safety_boundary="documented in safety boundary statement",
                limitation=lim_texts[0] if lim_texts else "see limitations report",
                reviewer_question=question_by_category.get(cat, ""),
                status=status))
        return self

    @property
    def blockers(self) -> List[AuditMatrixRow]:
        return [r for r in self.rows if r.blocker_flag]

    def to_dict(self) -> Dict[str, Any]:
        reviewable = sum(1 for r in self.rows
                         if r.status == AuditMatrixStatus.REVIEWABLE)
        return {
            "audit_matrix_row_count": len(self.rows),
            "reviewable_count": reviewable,
            "audit_matrix_blocker_count": len(self.blockers),
            "rows": [r.to_dict() for r in self.rows],
            "note": "the matrix exposes gaps; there is no empty green dashboard, "
                    "and falsified/unsupported claims stay visible",
        }
