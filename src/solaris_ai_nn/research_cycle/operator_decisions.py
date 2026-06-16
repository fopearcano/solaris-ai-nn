"""Operator decisions -- explicit local artifacts; never invented by Solaris.

:class:`OperatorDecisionRecord` records an operator's explicit decision (approve/
reject/request-revision/confirm/...). The system cannot invent operator approval,
operator approval cannot override a critical safety failure or erase missing
evidence, and operator rejection is preserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class OperatorDecisionType:
    APPROVE_EXPERIMENT_PACK_FOR_EXTERNAL_AGENT = \
        "approve_experiment_pack_for_external_agent"
    REJECT_EXPERIMENT_PACK = "reject_experiment_pack"
    REQUEST_REVISION = "request_revision"
    CONFIRM_EXTERNAL_IMPLEMENTATION_SUBMITTED = \
        "confirm_external_implementation_submitted"
    ACCEPT_INTAKE_RECOMMENDATION = "accept_intake_recommendation"
    REJECT_INTAKE_RECOMMENDATION = "reject_intake_recommendation"
    CONFIRM_EXTERNAL_MERGE = "confirm_external_merge"
    REJECT_MERGE = "reject_merge"
    APPROVE_CANDIDATE_BASELINE = "approve_candidate_baseline"
    REJECT_CANDIDATE_BASELINE = "reject_candidate_baseline"
    APPROVE_SOAK = "approve_soak"
    APPROVE_REPLICATION = "approve_replication"
    APPROVE_FALSIFICATION = "approve_falsification"
    ARCHIVE_CYCLE = "archive_cycle"
    START_NEXT_CYCLE = "start_next_cycle"

    ALL = (APPROVE_EXPERIMENT_PACK_FOR_EXTERNAL_AGENT, REJECT_EXPERIMENT_PACK,
           REQUEST_REVISION, CONFIRM_EXTERNAL_IMPLEMENTATION_SUBMITTED,
           ACCEPT_INTAKE_RECOMMENDATION, REJECT_INTAKE_RECOMMENDATION,
           CONFIRM_EXTERNAL_MERGE, REJECT_MERGE, APPROVE_CANDIDATE_BASELINE,
           REJECT_CANDIDATE_BASELINE, APPROVE_SOAK, APPROVE_REPLICATION,
           APPROVE_FALSIFICATION, ARCHIVE_CYCLE, START_NEXT_CYCLE)


class OperatorDecisionStatus:
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    PENDING = "pending"
    UNKNOWN = "unknown"

    ALL = (APPROVED, REJECTED, REVISION_REQUESTED, PENDING, UNKNOWN)


@dataclass
class OperatorDecisionRequirement:
    """A decision the operator must make for the cycle to proceed."""

    decision_type: str
    detail: str = ""
    blocking: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"decision_type": self.decision_type, "detail": self.detail,
                "blocking": self.blocking}


@dataclass
class OperatorDecisionRecord:
    """One explicit operator decision (local artifact; never auto-approved)."""

    decision_type: str
    status: str = OperatorDecisionStatus.PENDING
    operator_ref: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        if self.decision_type not in OperatorDecisionType.ALL:
            self.decision_type = OperatorDecisionType.REQUEST_REVISION
        if self.status not in OperatorDecisionStatus.ALL:
            self.status = OperatorDecisionStatus.UNKNOWN

    @property
    def approved(self) -> bool:
        return self.status == OperatorDecisionStatus.APPROVED

    @property
    def rejected(self) -> bool:
        return self.status == OperatorDecisionStatus.REJECTED

    def to_dict(self) -> Dict[str, Any]:
        return {"decision_type": self.decision_type, "status": self.status,
                "operator_ref": self.operator_ref, "detail": self.detail,
                "approved": self.approved, "rejected": self.rejected,
                "auto_approved": False, "invented_by_system": False}


def load_operator_decisions(records: Optional[List[Dict[str, Any]]],
                            ) -> List[OperatorDecisionRecord]:
    """Load explicit operator-decision records (only operator-provided)."""
    out: List[OperatorDecisionRecord] = []
    for r in records or []:
        out.append(OperatorDecisionRecord(
            decision_type=str(r.get("decision_type", "")),
            status=str(r.get("status", OperatorDecisionStatus.PENDING)),
            operator_ref=str(r.get("operator_ref", "")),
            detail=str(r.get("detail", ""))))
    return out


def required_decisions(bundle: Dict[str, Any],
                       decisions: List[OperatorDecisionRecord],
                       ) -> List[OperatorDecisionRequirement]:
    """Determine which operator decisions are still required (not auto-made)."""
    bundle = bundle or {}
    made = {d.decision_type for d in decisions
            if d.status != OperatorDecisionStatus.PENDING}
    reqs: List[OperatorDecisionRequirement] = []

    if bundle.get("experiment_compiler") and \
            OperatorDecisionType.APPROVE_EXPERIMENT_PACK_FOR_EXTERNAL_AGENT \
            not in made:
        reqs.append(OperatorDecisionRequirement(
            OperatorDecisionType.APPROVE_EXPERIMENT_PACK_FOR_EXTERNAL_AGENT,
            "approve the compiled experiment pack for an external agent"))
    if bundle.get("implementation_intake") and \
            OperatorDecisionType.CONFIRM_EXTERNAL_MERGE not in made:
        reqs.append(OperatorDecisionRequirement(
            OperatorDecisionType.CONFIRM_EXTERNAL_MERGE,
            "confirm the external human merge (outside Solaris)"))
    if bundle.get("post_merge") and \
            OperatorDecisionType.APPROVE_CANDIDATE_BASELINE not in made:
        reqs.append(OperatorDecisionRequirement(
            OperatorDecisionType.APPROVE_CANDIDATE_BASELINE,
            "approve (or reject) the candidate baseline"))
    rb = bundle.get("research_baseline", {}) or {}
    if rb.get("baseline_status") in ("validated", "validated_with_warnings") \
            and OperatorDecisionType.START_NEXT_CYCLE not in made:
        reqs.append(OperatorDecisionRequirement(
            OperatorDecisionType.START_NEXT_CYCLE,
            "approve soak/replication and start the next cycle",
            blocking=False))
    return reqs
