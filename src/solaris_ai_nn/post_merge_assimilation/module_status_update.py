"""Module status update recommendation -- metadata only; nothing is changed.

:class:`ModuleStatusUpdateRecommendationBuilder` recommends a status for the
candidate baseline / changed modules (keep experimental, validate, promote,
regression-watch, freeze, rollback, block). Recommendations are metadata only:
no module is actually changed and no source is modified. Safety-critical concerns
override promotion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ModuleStatusUpdateType:
    KEEP_EXPERIMENTAL = "keep_experimental"
    PROMOTE_CANDIDATE = "promote_candidate"
    VALIDATE_CANDIDATE = "validate_candidate"
    VALIDATE_WITH_WARNING = "validate_with_warning"
    RETEST_REQUIRED = "retest_required"
    REGRESSION_WATCH = "regression_watch"
    FREEZE_CANDIDATE = "freeze_candidate"
    ROLLBACK_RECOMMENDED = "rollback_recommended"
    BLOCK_DUE_TO_SAFETY = "block_due_to_safety"
    BLOCK_DUE_TO_FALSIFICATION = "block_due_to_falsification"
    UNKNOWN = "unknown"

    ALL = (KEEP_EXPERIMENTAL, PROMOTE_CANDIDATE, VALIDATE_CANDIDATE,
           VALIDATE_WITH_WARNING, RETEST_REQUIRED, REGRESSION_WATCH,
           FREEZE_CANDIDATE, ROLLBACK_RECOMMENDED, BLOCK_DUE_TO_SAFETY,
           BLOCK_DUE_TO_FALSIFICATION, UNKNOWN)


class ModuleStatusUpdateReason:
    TESTS_PASSED = "tests_passed"
    TESTS_FAILED = "tests_failed"
    SAFETY_PRESERVED = "safety_preserved"
    SAFETY_REGRESSED = "safety_regressed"
    SPEC_SATISFIED = "spec_satisfied"
    SPEC_INCOMPLETE = "spec_incomplete"
    EVIDENCE_MISSING = "evidence_missing"
    FALSIFICATION_PASSED = "falsification_passed"
    FALSIFICATION_FAILED = "falsification_failed"
    MINI_SOAK_IMPROVED = "mini_soak_improved"
    MINI_SOAK_REGRESSED = "mini_soak_regressed"
    REPLICATION_READY = "replication_ready"
    REGRESSION_DETECTED = "regression_detected"
    UNKNOWN = "unknown"


@dataclass
class ModuleStatusUpdateRecommendation:
    """A metadata-only recommended status for the candidate baseline."""

    update_type: str
    reasons: List[str] = field(default_factory=list)
    target_modules: List[str] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"update_type": self.update_type, "reasons": list(self.reasons),
                "target_modules": list(self.target_modules),
                "detail": self.detail, "metadata_only": True,
                "modifies_module": False, "modifies_source": False}


@dataclass
class ModuleStatusUpdateRecommendationBuilder:
    """Builds module-status recommendations from the post-merge evidence."""

    def build(self, *, evidence: Optional[Dict[str, Any]] = None,
              regression: Optional[Dict[str, Any]] = None,
              comparison: Optional[Dict[str, Any]] = None,
              intake: Optional[Dict[str, Any]] = None,
              validation: Optional[Dict[str, Any]] = None,
              target_modules: Optional[List[str]] = None,
              ) -> ModuleStatusUpdateRecommendation:
        evidence = evidence or {}
        regression = regression or {}
        comparison = comparison or {}
        intake = intake or {}
        validation = validation or {}
        reasons: List[str] = []

        critical_regression = regression.get("critical_regression_count", 0) > 0
        safety_negative = evidence.get("safety_negative", False)
        missing_required = validation.get("missing_validation_artifact_count",
                                          0) > 0
        # The intake "block due to safety" is *advisory*: it forces a safety
        # block only when the operator's separate safety evidence does not pass
        # (section 14). Passing safety-invariant evidence can clear it.
        safety_invariant_failed = self._artifact_passed(
            validation, "safety_invariant_run") is False

        # Falsification result (from validation artifacts).
        falsification = self._artifact_passed(validation, "falsification_replay")
        if falsification is True:
            reasons.append(ModuleStatusUpdateReason.FALSIFICATION_PASSED)
        elif falsification is False:
            reasons.append(ModuleStatusUpdateReason.FALSIFICATION_FAILED)

        # Decide (safety dominates -- from actual safety evidence).
        if safety_negative or safety_invariant_failed or \
                self._safety_dim_regressed(comparison):
            reasons.append(ModuleStatusUpdateReason.SAFETY_REGRESSED)
            update = ModuleStatusUpdateType.BLOCK_DUE_TO_SAFETY
        elif falsification is False:
            update = ModuleStatusUpdateType.BLOCK_DUE_TO_FALSIFICATION
        elif critical_regression:
            reasons.append(ModuleStatusUpdateReason.REGRESSION_DETECTED)
            update = ModuleStatusUpdateType.ROLLBACK_RECOMMENDED
        elif self._tests_failed(validation, intake):
            reasons.append(ModuleStatusUpdateReason.TESTS_FAILED)
            update = ModuleStatusUpdateType.RETEST_REQUIRED
        elif missing_required:
            reasons.append(ModuleStatusUpdateReason.EVIDENCE_MISSING)
            update = ModuleStatusUpdateType.RETEST_REQUIRED
        elif regression.get("major_regression_count", 0) > 0:
            reasons.append(ModuleStatusUpdateReason.REGRESSION_DETECTED)
            update = ModuleStatusUpdateType.REGRESSION_WATCH
        else:
            reasons.append(ModuleStatusUpdateReason.SAFETY_PRESERVED)
            reasons.append(ModuleStatusUpdateReason.TESTS_PASSED)
            if intake.get("spec_compliance_status") == "satisfied":
                reasons.append(ModuleStatusUpdateReason.SPEC_SATISFIED)
            if evidence.get("counts", {}).get("inconclusive", 0) or \
                    comparison.get("overall") == "mixed":
                update = ModuleStatusUpdateType.VALIDATE_WITH_WARNING
            elif self._artifact_passed(validation, "mini_soak") is True:
                reasons.append(ModuleStatusUpdateReason.MINI_SOAK_IMPROVED)
                reasons.append(ModuleStatusUpdateReason.REPLICATION_READY)
                update = ModuleStatusUpdateType.VALIDATE_CANDIDATE
            else:
                update = ModuleStatusUpdateType.VALIDATE_CANDIDATE
        return ModuleStatusUpdateRecommendation(
            update_type=update, reasons=reasons,
            target_modules=list(target_modules or []),
            detail="metadata-only recommendation; no module/source changed")

    @staticmethod
    def _artifact_passed(validation: Dict, atype: str):
        for a in validation.get("artifacts", []):
            if a.get("artifact_type") == atype and a.get("present"):
                return a.get("passed")
        return None

    @staticmethod
    def _tests_failed(validation: Dict, intake: Dict) -> bool:
        tests = ModuleStatusUpdateRecommendationBuilder._artifact_passed(
            validation, "full_test_run")
        if tests is False:
            return True
        return int(intake.get("test_failure_count", 0) or 0) > 0

    @staticmethod
    def _safety_dim_regressed(comparison: Dict) -> bool:
        return bool(comparison.get("safety_regressed"))
