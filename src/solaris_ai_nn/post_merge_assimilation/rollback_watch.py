"""Rollback watch -- a recommendation, never an execution.

:class:`RollbackWatch` derives a rollback recommendation from the post-merge
evidence (critical safety regression, failed tests, blocked claim, spec
noncompliance, resource blowup, falsification failure, mini-soak regression,
boundary violations, missing evidence, operator rejection). Rollback is a
recommendation only; it is never executed, and all failed artifacts are preserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RollbackWatchTrigger:
    CRITICAL_SAFETY_REGRESSION = "critical_safety_regression"
    FAILED_REQUIRED_TESTS = "failed_required_tests"
    CLAIMGUARD_BLOCKED_CLAIM = "claimguard_blocked_claim"
    SPEC_NONCOMPLIANCE = "spec_noncompliance"
    SEVERE_RESOURCE_BLOWUP = "severe_resource_blowup"
    FALSIFICATION_FAILURE = "falsification_failure"
    MINI_SOAK_REGRESSION = "mini_soak_regression"
    SOURCE_BOUNDARY_VIOLATION = "source_boundary_violation"
    SIMULATION_BOUNDARY_VIOLATION = "simulation_boundary_violation"
    MISSING_CRITICAL_EVIDENCE = "missing_critical_evidence"
    OPERATOR_REJECTION = "operator_rejection"

    ALL = (CRITICAL_SAFETY_REGRESSION, FAILED_REQUIRED_TESTS,
           CLAIMGUARD_BLOCKED_CLAIM, SPEC_NONCOMPLIANCE, SEVERE_RESOURCE_BLOWUP,
           FALSIFICATION_FAILURE, MINI_SOAK_REGRESSION,
           SOURCE_BOUNDARY_VIOLATION, SIMULATION_BOUNDARY_VIOLATION,
           MISSING_CRITICAL_EVIDENCE, OPERATOR_REJECTION)


class RollbackWatchRecommendation:
    NO_ROLLBACK_NEEDED = "no_rollback_needed"
    MONITOR = "monitor"
    REQUEST_REVISION = "request_revision"
    ROLLBACK_RECOMMENDED = "rollback_recommended"
    IMMEDIATE_OPERATOR_REVIEW = "immediate_operator_review"
    BLOCK_BASELINE = "block_baseline"

    ALL = (NO_ROLLBACK_NEEDED, MONITOR, REQUEST_REVISION, ROLLBACK_RECOMMENDED,
           IMMEDIATE_OPERATOR_REVIEW, BLOCK_BASELINE)


@dataclass
class RollbackWatchResult:
    """The rollback-watch recommendation (documented, never executed)."""

    recommendation: str = RollbackWatchRecommendation.NO_ROLLBACK_NEEDED
    triggers: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation": self.recommendation,
            "triggers": list(self.triggers),
            "rollback_watch_trigger_count": len(self.triggers),
            "steps": list(self.steps),
            "executed": False, "preserves_evidence": True,
            "note": "rollback is a recommendation only; it is never executed "
                    "and all failed artifacts are preserved",
        }


@dataclass
class RollbackWatch:
    """Builds a rollback-watch recommendation from the post-merge evidence."""

    def build(self, *, regression: Optional[Dict[str, Any]] = None,
              evidence: Optional[Dict[str, Any]] = None,
              intake: Optional[Dict[str, Any]] = None,
              validation: Optional[Dict[str, Any]] = None,
              manifest: Optional[Dict[str, Any]] = None,
              ) -> RollbackWatchResult:
        regression = regression or {}
        evidence = evidence or {}
        intake = intake or {}
        validation = validation or {}
        manifest = manifest or {}
        result = RollbackWatchResult()

        if regression.get("critical_regression_count", 0) > 0 or \
                evidence.get("safety_negative"):
            result.triggers.append(
                RollbackWatchTrigger.CRITICAL_SAFETY_REGRESSION)
        if self._artifact_passed(validation, "full_test_run") is False or \
                int(intake.get("test_failure_count", 0) or 0) > 0:
            result.triggers.append(RollbackWatchTrigger.FAILED_REQUIRED_TESTS)
        if intake.get("claimguard_finding_count", 0) and \
                intake.get("merge_recommendation_status") == \
                "block_merge_due_to_safety":
            result.triggers.append(RollbackWatchTrigger.CLAIMGUARD_BLOCKED_CLAIM)
        if intake.get("spec_compliance_status") == "blocked":
            result.triggers.append(RollbackWatchTrigger.SPEC_NONCOMPLIANCE)
        if self._artifact_passed(validation, "falsification_replay") is False:
            result.triggers.append(RollbackWatchTrigger.FALSIFICATION_FAILURE)
        if self._artifact_passed(validation, "mini_soak") is False:
            result.triggers.append(RollbackWatchTrigger.MINI_SOAK_REGRESSION)
        if int(intake.get("forbidden_file_change_count", 0) or 0) > 0:
            result.triggers.append(
                RollbackWatchTrigger.SOURCE_BOUNDARY_VIOLATION)
        if validation.get("missing_validation_artifact_count", 0) > 0:
            result.triggers.append(
                RollbackWatchTrigger.MISSING_CRITICAL_EVIDENCE)
        if manifest.get("operator_notes", "").lower().find("reject") >= 0:
            result.triggers.append(RollbackWatchTrigger.OPERATOR_REJECTION)

        result.recommendation = self._recommend(result.triggers, regression,
                                                 evidence)
        if result.recommendation != RollbackWatchRecommendation.NO_ROLLBACK_NEEDED:
            result.steps = [
                "record the triggering finding(s) as evidence",
                "do NOT delete the failed branch artifacts, reports, or logs",
                "the operator reverts the external change manually if needed",
                "collect any missing validation evidence",
                "re-run the post-merge assimilation after revision"]
        return result

    @staticmethod
    def _recommend(triggers: List[str], regression: Dict,
                   evidence: Dict) -> str:
        if not triggers:
            return RollbackWatchRecommendation.NO_ROLLBACK_NEEDED
        if (RollbackWatchTrigger.CRITICAL_SAFETY_REGRESSION in triggers or
                RollbackWatchTrigger.SOURCE_BOUNDARY_VIOLATION in triggers):
            return RollbackWatchRecommendation.ROLLBACK_RECOMMENDED
        if RollbackWatchTrigger.FAILED_REQUIRED_TESTS in triggers or \
                RollbackWatchTrigger.FALSIFICATION_FAILURE in triggers:
            return RollbackWatchRecommendation.REQUEST_REVISION
        if RollbackWatchTrigger.MISSING_CRITICAL_EVIDENCE in triggers:
            return RollbackWatchRecommendation.MONITOR
        if regression.get("major_regression_count", 0) > 0:
            return RollbackWatchRecommendation.IMMEDIATE_OPERATOR_REVIEW
        return RollbackWatchRecommendation.MONITOR

    @staticmethod
    def _artifact_passed(validation: Dict, atype: str):
        for a in validation.get("artifacts", []):
            if a.get("artifact_type") == atype and a.get("present"):
                return a.get("passed")
        return None
