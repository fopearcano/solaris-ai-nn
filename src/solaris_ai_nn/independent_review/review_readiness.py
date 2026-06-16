"""Independent review readiness -- inspectability, not claim strength.

:class:`IndependentReviewReadinessEvaluator` decides whether the local evidence
package is ready for internal, friendly external, or hostile external review.
Hostile-review readiness requires strong documentation, not strong claims; a weak
or negative result can still be review-ready if documented honestly; and an
asserted forbidden claim blocks readiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReviewReadinessStatus:
    READY_FOR_INTERNAL_REVIEW = "ready_for_internal_review"
    READY_FOR_FRIENDLY_EXTERNAL_REVIEW = "ready_for_friendly_external_review"
    READY_FOR_HOSTILE_EXTERNAL_REVIEW = "ready_for_hostile_external_review"
    READY_WITH_MAJOR_LIMITATIONS = "ready_with_major_limitations"
    NOT_READY_MISSING_ARTIFACTS = "not_ready_missing_artifacts"
    NOT_READY_SANITIZATION_FAILED = "not_ready_sanitization_failed"
    NOT_READY_CLAIMS_UNSUPPORTED = "not_ready_claims_unsupported"
    NOT_READY_SAFETY_BOUNDARY_MISSING = "not_ready_safety_boundary_missing"
    BLOCKED_BY_FORBIDDEN_CLAIMS = "blocked_by_forbidden_claims"
    INCONCLUSIVE = "inconclusive"

    ALL = (READY_FOR_INTERNAL_REVIEW, READY_FOR_FRIENDLY_EXTERNAL_REVIEW,
           READY_FOR_HOSTILE_EXTERNAL_REVIEW, READY_WITH_MAJOR_LIMITATIONS,
           NOT_READY_MISSING_ARTIFACTS, NOT_READY_SANITIZATION_FAILED,
           NOT_READY_CLAIMS_UNSUPPORTED, NOT_READY_SAFETY_BOUNDARY_MISSING,
           BLOCKED_BY_FORBIDDEN_CLAIMS, INCONCLUSIVE)


class ReviewReadinessBlockerType:
    MISSING_CRITICAL_ARTIFACT = "missing_critical_artifact"
    SANITIZER_CRITICAL = "sanitizer_critical_finding"
    FORBIDDEN_CLAIM_ASSERTED = "forbidden_claim_asserted"
    SAFETY_BOUNDARY_MISSING = "safety_boundary_missing"
    NO_SUPPORTED_OR_DOCUMENTED_CLAIM = "no_supported_or_documented_claim"
    STRONG_ALTERNATIVE_EXPLANATION = "strong_alternative_explanation"
    UNRESOLVED_OBJECTION = "unresolved_objection"
    MISSING_REPRODUCIBILITY = "missing_reproducibility_commands"

    ALL = (MISSING_CRITICAL_ARTIFACT, SANITIZER_CRITICAL,
           FORBIDDEN_CLAIM_ASSERTED, SAFETY_BOUNDARY_MISSING,
           NO_SUPPORTED_OR_DOCUMENTED_CLAIM, STRONG_ALTERNATIVE_EXPLANATION,
           UNRESOLVED_OBJECTION, MISSING_REPRODUCIBILITY)


@dataclass
class ReviewReadinessBlocker:
    """One readiness blocker (advisory)."""

    blocker_type: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"blocker_type": self.blocker_type, "detail": self.detail}


@dataclass
class IndependentReviewReadiness:
    """The advisory readiness result."""

    status: str
    blockers: List[ReviewReadinessBlocker] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "review_readiness_status": self.status,
            "review_readiness_blocker_count": len(self.blockers),
            "blockers": [b.to_dict() for b in self.blockers],
            "detail": self.detail,
            "note": "readiness means the evidence is inspectable, not that the "
                    "claims are strong; a weak or negative result can still be "
                    "review-ready if documented honestly",
        }


@dataclass
class IndependentReviewReadinessEvaluator:
    """Evaluates review readiness from the assembled review material."""

    def evaluate(self, *,
                 manifest: Dict[str, Any],
                 sanitizer: Dict[str, Any],
                 claim_registry: Dict[str, Any],
                 forbidden: Dict[str, Any],
                 adversarial: Dict[str, Any],
                 audit_matrix: Dict[str, Any],
                 response_ledger: Dict[str, Any],
                 challenges: Dict[str, Any],
                 safety_boundary_present: bool,
                 ) -> IndependentReviewReadiness:
        blockers: List[ReviewReadinessBlocker] = []

        # Hard blocks first.
        if forbidden.get("blocks_publication") or \
                forbidden.get("asserted_forbidden_count", 0) > 0:
            blockers.append(ReviewReadinessBlocker(
                ReviewReadinessBlockerType.FORBIDDEN_CLAIM_ASSERTED,
                "an asserted forbidden claim is present"))
            return IndependentReviewReadiness(
                ReviewReadinessStatus.BLOCKED_BY_FORBIDDEN_CLAIMS, blockers,
                "forbidden claim assertion blocks all review readiness")

        if sanitizer.get("blocks_readiness"):
            blockers.append(ReviewReadinessBlocker(
                ReviewReadinessBlockerType.SANITIZER_CRITICAL,
                f"{sanitizer.get('critical_sanitizer_finding_count', 0)} "
                "critical sanitizer finding(s)"))
            return IndependentReviewReadiness(
                ReviewReadinessStatus.NOT_READY_SANITIZATION_FAILED, blockers,
                "critical sanitizer findings must be redacted by the operator")

        if manifest.get("missing_critical_artifact_count", 0) > 0:
            blockers.append(ReviewReadinessBlocker(
                ReviewReadinessBlockerType.MISSING_CRITICAL_ARTIFACT,
                f"{manifest.get('missing_critical_artifact_count', 0)} critical "
                "artifact(s) missing"))
            return IndependentReviewReadiness(
                ReviewReadinessStatus.NOT_READY_MISSING_ARTIFACTS, blockers,
                "critical review artifacts are missing")

        if not safety_boundary_present:
            blockers.append(ReviewReadinessBlocker(
                ReviewReadinessBlockerType.SAFETY_BOUNDARY_MISSING,
                "no safety boundary statement available"))
            return IndependentReviewReadiness(
                ReviewReadinessStatus.NOT_READY_SAFETY_BOUNDARY_MISSING,
                blockers, "a documented safety boundary is required")

        # Soft factors below: documentation, not claim strength.
        supported = claim_registry.get("supported_claim_count", 0) + \
            claim_registry.get("weakly_supported_claim_count", 0) + \
            claim_registry.get("partially_supported_claim_count", 0)
        documented = claim_registry.get("scientific_claim_count", 0) > 0
        if not documented:
            blockers.append(ReviewReadinessBlocker(
                ReviewReadinessBlockerType.NO_SUPPORTED_OR_DOCUMENTED_CLAIM,
                "no claims documented at all"))
            return IndependentReviewReadiness(
                ReviewReadinessStatus.NOT_READY_CLAIMS_UNSUPPORTED, blockers,
                "no documented claims to review")

        strong_alt = adversarial.get("strong_alternative_count", 0)
        if strong_alt:
            blockers.append(ReviewReadinessBlocker(
                ReviewReadinessBlockerType.STRONG_ALTERNATIVE_EXPLANATION,
                f"{strong_alt} strong alternative explanation(s) outstanding"))
        unresolved = response_ledger.get("unresolved_objection_count", 0)
        if unresolved:
            blockers.append(ReviewReadinessBlocker(
                ReviewReadinessBlockerType.UNRESOLVED_OBJECTION,
                f"{unresolved} unresolved objection(s)"))
        if challenges.get("available_challenge_count", 0) == 0:
            blockers.append(ReviewReadinessBlocker(
                ReviewReadinessBlockerType.MISSING_REPRODUCIBILITY,
                "no reproducibility challenge is currently runnable"))

        # Determine the readiness tier from documentation completeness.
        matrix_blockers = audit_matrix.get("audit_matrix_blocker_count", 0)
        major_limitations = strong_alt > 0 or unresolved > 0
        sanitizer_warnings = sanitizer.get("sanitizer_finding_count", 0) > 0

        if not blockers and not sanitizer_warnings:
            status = ReviewReadinessStatus.READY_FOR_HOSTILE_EXTERNAL_REVIEW
        elif major_limitations:
            status = ReviewReadinessStatus.READY_WITH_MAJOR_LIMITATIONS
        elif sanitizer_warnings or matrix_blockers:
            status = ReviewReadinessStatus.READY_FOR_FRIENDLY_EXTERNAL_REVIEW
        else:
            status = ReviewReadinessStatus.READY_FOR_INTERNAL_REVIEW

        detail = ("ready for review at the indicated tier; readiness reflects "
                  "documentation quality, not claim strength")
        return IndependentReviewReadiness(status, blockers, detail)
