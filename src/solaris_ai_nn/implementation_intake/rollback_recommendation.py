"""Rollback recommendation -- documentation only; never executed.

:class:`RollbackRecommendationBuilder` produces a documented
:class:`RollbackRecommendation` when an implementation should be reverted. It
never executes a rollback and every recommendation preserves the failed
artifacts as evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RollbackRecommendationReason:
    SAFETY_REGRESSION = "safety_regression"
    FAILED_TESTS = "failed_tests"
    SPEC_MISMATCH = "spec_mismatch"
    UNEXPECTED_FILE_CHANGES = "unexpected_file_changes"
    UNSUPPORTED_CLAIMS = "unsupported_claims"
    RESOURCE_BLOWUP = "resource_blowup"
    MISSING_ROLLBACK_PLAN = "missing_rollback_plan"
    MISSING_VALIDATION_PLAN = "missing_validation_plan"
    OPERATOR_REJECTION = "operator_rejection"
    INCONCLUSIVE_EVIDENCE = "inconclusive_evidence"

    ALL = (SAFETY_REGRESSION, FAILED_TESTS, SPEC_MISMATCH,
           UNEXPECTED_FILE_CHANGES, UNSUPPORTED_CLAIMS, RESOURCE_BLOWUP,
           MISSING_ROLLBACK_PLAN, MISSING_VALIDATION_PLAN, OPERATOR_REJECTION,
           INCONCLUSIVE_EVIDENCE)


class RollbackUrgency:
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    IMMEDIATE = "immediate"

    ALL = (NONE, LOW, MODERATE, HIGH, IMMEDIATE)


@dataclass
class RollbackRecommendation:
    """A documented (never executed) rollback recommendation."""

    recommended: bool = False
    urgency: str = RollbackUrgency.NONE
    reasons: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommended": self.recommended, "urgency": self.urgency,
            "reasons": list(self.reasons), "steps": list(self.steps),
            "executed": False, "preserves_evidence": True,
            "note": "documentation only; rollback is never executed and failed "
                    "artifacts are preserved as evidence",
        }


@dataclass
class RollbackRecommendationBuilder:
    """Builds a rollback recommendation from the audit results."""

    def build(self, *, merge_recommendation: Optional[Dict] = None,
              safety_regression: Optional[Dict] = None,
              test_audit: Optional[Dict] = None,
              spec_compliance: Optional[Dict] = None,
              diff_audit: Optional[Dict] = None,
              claimguard_audit: Optional[Dict] = None,
              manifest: Optional[Dict] = None) -> RollbackRecommendation:
        merge_recommendation = merge_recommendation or {}
        safety_regression = safety_regression or {}
        test_audit = test_audit or {}
        spec_compliance = spec_compliance or {}
        diff_audit = diff_audit or {}
        claimguard_audit = claimguard_audit or {}
        manifest = manifest or {}

        rec = RollbackRecommendation()
        if safety_regression.get("critical_count", 0):
            rec.reasons.append(RollbackRecommendationReason.SAFETY_REGRESSION)
        if test_audit and not test_audit.get("passes", True):
            rec.reasons.append(RollbackRecommendationReason.FAILED_TESTS)
        if spec_compliance.get("blocking_failure_count", 0):
            rec.reasons.append(RollbackRecommendationReason.SPEC_MISMATCH)
        if diff_audit.get("forbidden_file_change_count", 0) or \
                diff_audit.get("unexpected_file_change_count", 0):
            rec.reasons.append(
                RollbackRecommendationReason.UNEXPECTED_FILE_CHANGES)
        if claimguard_audit.get("blocks_readiness"):
            rec.reasons.append(RollbackRecommendationReason.UNSUPPORTED_CLAIMS)
        missing = set(manifest.get("blockers", []))
        if "rollback_plan" in missing:
            rec.reasons.append(
                RollbackRecommendationReason.MISSING_ROLLBACK_PLAN)
        if "validation_plan" in missing:
            rec.reasons.append(
                RollbackRecommendationReason.MISSING_VALIDATION_PLAN)
        status = merge_recommendation.get("status", "")
        if status == "inconclusive":
            rec.reasons.append(
                RollbackRecommendationReason.INCONCLUSIVE_EVIDENCE)

        rec.recommended = bool(rec.reasons)
        rec.urgency = self._urgency(safety_regression, rec)
        if rec.recommended:
            rec.steps = [
                "stop and record the triggering finding(s) as evidence",
                "do NOT delete the failed branch artifacts, reports, or logs",
                "the operator reverts the change manually (git revert/restore)",
                "archive the implementation summary with the audit reports",
                "register the failure as future architecture/replication "
                "evidence"]
        return rec

    @staticmethod
    def _urgency(safety_regression: Dict, rec: RollbackRecommendation) -> str:
        if safety_regression.get("critical_count", 0):
            return RollbackUrgency.IMMEDIATE
        if RollbackRecommendationReason.FAILED_TESTS in rec.reasons or \
                RollbackRecommendationReason.SPEC_MISMATCH in rec.reasons:
            return RollbackUrgency.HIGH
        if rec.reasons:
            return RollbackUrgency.MODERATE
        return RollbackUrgency.NONE
