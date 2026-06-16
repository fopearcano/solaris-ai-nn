"""Baseline validation summary -- the evidence behind a validated status.

:class:`BaselineValidationSummary` summarizes the validation evidence per
dimension (unit/integration/safety tests, examples, ClaimGuard, safety
invariants, mini soak, falsification replay, replication registry, post-merge
validation, documentation, operator review). A safety failure blocks validation;
missing required validation blocks validation; warnings remain visible; and
passing tests do not prove scientific claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ValidationStatus:
    PASSED = "passed"
    PASSED_WITH_WARNINGS = "passed_with_warnings"
    FAILED = "failed"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"

    ALL = (PASSED, PASSED_WITH_WARNINGS, FAILED, MISSING, NOT_APPLICABLE,
           UNKNOWN)


class ValidationDimension:
    UNIT_TESTS = "unit_tests"
    INTEGRATION_TESTS = "integration_tests"
    SAFETY_TESTS = "safety_tests"
    EXAMPLE_RUNS = "example_runs"
    CLAIMGUARD = "claimguard"
    SAFETY_INVARIANTS = "safety_invariants"
    MINI_SOAK = "mini_soak"
    FALSIFICATION_REPLAY = "falsification_replay"
    REPLICATION_REGISTRY = "replication_registry"
    POST_MERGE_VALIDATION = "post_merge_validation"
    DOCUMENTATION = "documentation"
    OPERATOR_REVIEW = "operator_review"

    ALL = (UNIT_TESTS, INTEGRATION_TESTS, SAFETY_TESTS, EXAMPLE_RUNS,
           CLAIMGUARD, SAFETY_INVARIANTS, MINI_SOAK, FALSIFICATION_REPLAY,
           REPLICATION_REGISTRY, POST_MERGE_VALIDATION, DOCUMENTATION,
           OPERATOR_REVIEW)

    # Dimensions whose failure/absence blocks validation.
    REQUIRED = (SAFETY_TESTS, SAFETY_INVARIANTS, CLAIMGUARD, UNIT_TESTS)


@dataclass
class BaselineValidationSummary:
    """Per-dimension validation status; safety failures block validation."""

    statuses: Dict[str, str] = field(default_factory=dict)
    detail: Dict[str, str] = field(default_factory=dict)

    def build(self, *, validation_results: Optional[Dict[str, Any]] = None,
              intake: Optional[Dict[str, Any]] = None,
              ) -> "BaselineValidationSummary":
        vr = validation_results or {}
        intake = intake or {}
        mapping = {
            ValidationDimension.UNIT_TESTS: vr.get("unit_tests"),
            ValidationDimension.INTEGRATION_TESTS: vr.get("integration_tests"),
            ValidationDimension.SAFETY_TESTS: vr.get("safety_tests"),
            ValidationDimension.EXAMPLE_RUNS: vr.get("example_runs"),
            ValidationDimension.CLAIMGUARD: vr.get("claimguard"),
            ValidationDimension.SAFETY_INVARIANTS: vr.get("safety_invariants"),
            ValidationDimension.MINI_SOAK: vr.get("mini_soak"),
            ValidationDimension.FALSIFICATION_REPLAY:
                vr.get("falsification_replay"),
            ValidationDimension.REPLICATION_REGISTRY:
                vr.get("replication_registry"),
            ValidationDimension.POST_MERGE_VALIDATION:
                vr.get("post_merge_validation"),
            ValidationDimension.DOCUMENTATION: vr.get("documentation"),
            ValidationDimension.OPERATOR_REVIEW: vr.get("operator_review"),
        }
        for dim, value in mapping.items():
            self.statuses[dim] = self._status_of(value)
        return self

    @staticmethod
    def _status_of(value: Any) -> str:
        if value is None:
            return ValidationStatus.MISSING
        if isinstance(value, str) and value in ValidationStatus.ALL:
            return value
        if isinstance(value, dict):
            if value.get("failed"):
                return ValidationStatus.FAILED
            if value.get("warnings"):
                return ValidationStatus.PASSED_WITH_WARNINGS
            if value.get("passed") or value.get("safe") or value.get("ran"):
                return ValidationStatus.PASSED
            return ValidationStatus.UNKNOWN
        if value is True:
            return ValidationStatus.PASSED
        if value is False:
            return ValidationStatus.FAILED
        return ValidationStatus.UNKNOWN

    @property
    def safety_failed(self) -> bool:
        return any(self.statuses.get(d) == ValidationStatus.FAILED
                   for d in (ValidationDimension.SAFETY_TESTS,
                             ValidationDimension.SAFETY_INVARIANTS,
                             ValidationDimension.CLAIMGUARD))

    @property
    def required_missing(self) -> List[str]:
        return [d for d in ValidationDimension.REQUIRED
                if self.statuses.get(d) in (ValidationStatus.MISSING,
                                            ValidationStatus.UNKNOWN)]

    @property
    def required_failed(self) -> List[str]:
        return [d for d in ValidationDimension.REQUIRED
                if self.statuses.get(d) == ValidationStatus.FAILED]

    @property
    def blocks_validation(self) -> bool:
        return self.safety_failed or bool(self.required_missing) or \
            bool(self.required_failed)

    @property
    def has_warnings(self) -> bool:
        return any(s == ValidationStatus.PASSED_WITH_WARNINGS
                   for s in self.statuses.values())

    def counts(self) -> Dict[str, int]:
        out = {s: 0 for s in ValidationStatus.ALL}
        for s in self.statuses.values():
            out[s] = out.get(s, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        counts = self.counts()
        return {
            "statuses": dict(self.statuses),
            "counts": counts,
            "validation_pass_count": counts[ValidationStatus.PASSED]
            + counts[ValidationStatus.PASSED_WITH_WARNINGS],
            "validation_missing_count": counts[ValidationStatus.MISSING],
            "safety_failed": self.safety_failed,
            "required_missing": self.required_missing,
            "required_failed": self.required_failed,
            "blocks_validation": self.blocks_validation,
            "has_warnings": self.has_warnings,
            "note": "a safety failure or missing required validation blocks "
                    "validation; passing tests do not prove scientific claims",
        }
