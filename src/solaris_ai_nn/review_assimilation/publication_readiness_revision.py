"""Publication readiness revision -- advisory; critical objections block.

:class:`PublicationReadinessReviser` revises the publication readiness in light of
review feedback. Readiness is advisory and no publication occurs; critical
unresolved objections, forbidden claims, failed reproductions, or missing critical
evidence block readiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class PublicationReadinessImpact:
    IMPROVE_READINESS = "improve_readiness"
    DOWNGRADE_READINESS = "downgrade_readiness"
    BLOCK_PUBLICATION = "block_publication"
    READY_ONLY_AS_INTERNAL_REPORT = "ready_only_as_internal_report"
    READY_WITH_MAJOR_LIMITATIONS = "ready_with_major_limitations"
    REQUIRES_MORE_REVIEW = "requires_more_review"
    UNKNOWN = "unknown"

    ALL = (IMPROVE_READINESS, DOWNGRADE_READINESS, BLOCK_PUBLICATION,
           READY_ONLY_AS_INTERNAL_REPORT, READY_WITH_MAJOR_LIMITATIONS,
           REQUIRES_MORE_REVIEW, UNKNOWN)


class PublicationReadinessBlockerType:
    FORBIDDEN_CLAIM = "forbidden_claim"
    FAILED_REPRODUCTION = "failed_reproduction"
    MISSING_ARTIFACT = "missing_artifact"
    UNRESOLVED_CRITICAL_OBJECTION = "unresolved_critical_objection"
    SAFETY_BOUNDARY_MISSING = "safety_boundary_missing"
    COUNTEREVIDENCE_NOT_ADDRESSED = "counterevidence_not_addressed"
    CLAIM_TOO_STRONG = "claim_too_strong"
    METHOD_UNCLEAR = "method_unclear"
    LIMITATION_MISSING = "limitation_missing"
    UNKNOWN = "unknown"

    ALL = (FORBIDDEN_CLAIM, FAILED_REPRODUCTION, MISSING_ARTIFACT,
           UNRESOLVED_CRITICAL_OBJECTION, SAFETY_BOUNDARY_MISSING,
           COUNTEREVIDENCE_NOT_ADDRESSED, CLAIM_TOO_STRONG, METHOD_UNCLEAR,
           LIMITATION_MISSING, UNKNOWN)


@dataclass
class PublicationReadinessBlocker:
    """One readiness blocker (advisory)."""

    blocker_type: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"blocker_type": self.blocker_type, "detail": self.detail}


@dataclass
class PublicationReadinessRevision:
    """The revised, advisory publication readiness."""

    impact: str
    blockers: List[PublicationReadinessBlocker] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "publication_readiness_impact": self.impact,
            "publication_readiness_blocker_count": len(self.blockers),
            "blockers": [b.to_dict() for b in self.blockers],
            "detail": self.detail, "publishes": False, "advisory": True,
            "note": "publication readiness is advisory; no publication occurs and "
                    "critical unresolved objections block readiness",
        }


@dataclass
class PublicationReadinessReviser:
    """Revises publication readiness from the assimilated review feedback."""

    def revise(self, *, objection_summary: Dict[str, Any],
               claim_impact_summary: Dict[str, Any],
               reproduction_summary: Dict[str, Any],
               evidence_gap_map: Dict[str, Any],
               forbidden_asserted: bool = False,
               safety_boundary_present: bool = True,
               ) -> PublicationReadinessRevision:
        blockers: List[PublicationReadinessBlocker] = []

        if forbidden_asserted or claim_impact_summary.get(
                "claim_forbidden_count", 0) > 0:
            blockers.append(PublicationReadinessBlocker(
                PublicationReadinessBlockerType.FORBIDDEN_CLAIM,
                "a forbidden claim risk was raised in review"))
        if objection_summary.get("critical_unresolved_count", 0) > 0:
            blockers.append(PublicationReadinessBlocker(
                PublicationReadinessBlockerType.UNRESOLVED_CRITICAL_OBJECTION,
                f"{objection_summary['critical_unresolved_count']} unresolved "
                "critical objection(s)"))
        if reproduction_summary.get("reproduction_failure_count", 0) > 0:
            blockers.append(PublicationReadinessBlocker(
                PublicationReadinessBlockerType.FAILED_REPRODUCTION,
                f"{reproduction_summary['reproduction_failure_count']} failed "
                "reproduction(s)"))
        if claim_impact_summary.get("claim_falsification_count", 0) > 0:
            blockers.append(PublicationReadinessBlocker(
                PublicationReadinessBlockerType.COUNTEREVIDENCE_NOT_ADDRESSED,
                "a claim was falsified under review"))
        if evidence_gap_map.get("critical_evidence_gap_count", 0) > 0:
            blockers.append(PublicationReadinessBlocker(
                PublicationReadinessBlockerType.MISSING_ARTIFACT,
                f"{evidence_gap_map['critical_evidence_gap_count']} critical "
                "evidence gap(s)"))
        if not safety_boundary_present:
            blockers.append(PublicationReadinessBlocker(
                PublicationReadinessBlockerType.SAFETY_BOUNDARY_MISSING,
                "no safety boundary statement available"))

        # Determine the impact.
        hard_blockers = [b for b in blockers if b.blocker_type in (
            PublicationReadinessBlockerType.FORBIDDEN_CLAIM,
            PublicationReadinessBlockerType.UNRESOLVED_CRITICAL_OBJECTION,
            PublicationReadinessBlockerType.SAFETY_BOUNDARY_MISSING)]
        if hard_blockers:
            impact = PublicationReadinessImpact.BLOCK_PUBLICATION
            detail = "critical unresolved review blockers prevent publication"
        elif blockers:
            impact = PublicationReadinessImpact.READY_ONLY_AS_INTERNAL_REPORT
            detail = ("outstanding review findings limit readiness to an internal "
                      "report")
        elif claim_impact_summary.get("claim_downgrade_count", 0) > 0:
            impact = PublicationReadinessImpact.READY_WITH_MAJOR_LIMITATIONS
            detail = "claims were downgraded; readiness with major limitations"
        elif objection_summary.get("unresolved_objection_count", 0) > 0:
            impact = PublicationReadinessImpact.REQUIRES_MORE_REVIEW
            detail = "open objections remain; more review is needed"
        else:
            impact = PublicationReadinessImpact.IMPROVE_READINESS
            detail = "review raised no blocking findings"
        return PublicationReadinessRevision(impact=impact, blockers=blockers,
                                            detail=detail)
