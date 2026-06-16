"""Baseline limitation registry -- limitations are part of the baseline.

:class:`BaselineLimitationRegistry` records the baseline's known limitations with
a severity. A critical limitation blocks validated status; a major limitation
permits validated-with-warnings only if safety is preserved. Limitations are kept
operator-visible -- never buried inside prose.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class LimitationSeverity:
    INFO = "info"
    WARNING = "warning"
    MAJOR = "major"
    CRITICAL = "critical"

    ALL = (INFO, WARNING, MAJOR, CRITICAL)
    _RANK = {INFO: 0, WARNING: 1, MAJOR: 2, CRITICAL: 3}


class LimitationCategory:
    MISSING_EVIDENCE = "missing_evidence"
    INSUFFICIENT_REPLICATION = "insufficient_replication"
    FAILED_FALSIFICATION = "failed_falsification"
    FIXTURE_OVERFIT_RISK = "fixture_overfit_risk"
    HUMAN_LABEL_CONTAMINATION_RISK = "human_label_contamination_risk"
    MISSING_LIVE_DATA = "missing_live_data"
    WEAK_SAFETY_EVIDENCE = "weak_safety_evidence"
    WEAK_TEST_EVIDENCE = "weak_test_evidence"
    WEAK_SOAK_EVIDENCE = "weak_soak_evidence"
    WEAK_DEVELOPMENTAL_EVIDENCE = "weak_developmental_evidence"
    RESOURCE_CONSTRAINT = "resource_constraint"
    UNCLEAR_MODULE_EFFECT = "unclear_module_effect"
    UNRESOLVED_REGRESSION = "unresolved_regression"
    UNRESOLVED_BLOCKER = "unresolved_blocker"
    UNKNOWN = "unknown"

    ALL = (MISSING_EVIDENCE, INSUFFICIENT_REPLICATION, FAILED_FALSIFICATION,
           FIXTURE_OVERFIT_RISK, HUMAN_LABEL_CONTAMINATION_RISK,
           MISSING_LIVE_DATA, WEAK_SAFETY_EVIDENCE, WEAK_TEST_EVIDENCE,
           WEAK_SOAK_EVIDENCE, WEAK_DEVELOPMENTAL_EVIDENCE, RESOURCE_CONSTRAINT,
           UNCLEAR_MODULE_EFFECT, UNRESOLVED_REGRESSION, UNRESOLVED_BLOCKER,
           UNKNOWN)


@dataclass
class BaselineLimitation:
    """One operator-visible limitation of the baseline."""

    category: str
    severity: str
    detail: str = ""
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "severity": self.severity,
                "detail": self.detail, "evidence_refs": list(self.evidence_refs)}


@dataclass
class BaselineLimitationRegistry:
    """Holds the baseline's limitations; critical ones block validation."""

    limitations: List[BaselineLimitation] = field(default_factory=list)

    def add(self, category: str, severity: str, *, detail: str = "",
            evidence_refs: List[str] = None) -> None:
        if category not in LimitationCategory.ALL:
            category = LimitationCategory.UNKNOWN
        if severity not in LimitationSeverity.ALL:
            severity = LimitationSeverity.WARNING
        self.limitations.append(BaselineLimitation(
            category=category, severity=severity, detail=detail,
            evidence_refs=list(evidence_refs or [])))

    @property
    def critical_count(self) -> int:
        return sum(1 for l in self.limitations
                   if l.severity == LimitationSeverity.CRITICAL)

    @property
    def major_count(self) -> int:
        return sum(1 for l in self.limitations
                   if l.severity == LimitationSeverity.MAJOR)

    @property
    def blocks_validation(self) -> bool:
        return self.critical_count > 0

    @property
    def warnings_only(self) -> bool:
        return self.critical_count == 0 and self.major_count > 0

    def counts(self) -> Dict[str, int]:
        out = {s: 0 for s in LimitationSeverity.ALL}
        for l in self.limitations:
            out[l.severity] = out.get(l.severity, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "limitation_count": len(self.limitations),
            "limitations": [l.to_dict() for l in self.limitations],
            "counts": self.counts(),
            "critical_limitation_count": self.critical_count,
            "major_limitation_count": self.major_count,
            "blocks_validation": self.blocks_validation,
            "note": "limitations are part of the baseline; a critical "
                    "limitation blocks validated status and limitations are "
                    "kept operator-visible, never buried in prose",
        }


def build_limitation_registry(*, post_merge: Dict[str, Any],
                              intake: Dict[str, Any],
                              snapshot: Dict[str, Any],
                              validation: Dict[str, Any],
                              ) -> BaselineLimitationRegistry:
    """Derive the limitation registry from the post-merge + intake evidence."""
    reg = BaselineLimitationRegistry()
    post_merge = post_merge or {}
    intake = intake or {}
    snapshot = snapshot or {}
    validation = validation or {}

    # Unresolved regressions / blockers from the post-merge ledger.
    if int(post_merge.get("critical_regression_count", 0) or 0) > 0:
        reg.add(LimitationCategory.UNRESOLVED_REGRESSION,
                LimitationSeverity.CRITICAL,
                detail="critical regression recorded post-merge",
                evidence_refs=["post_merge:regression_watch"])
    elif int(post_merge.get("baseline_regression_count", 0) or 0) > 0:
        reg.add(LimitationCategory.UNRESOLVED_REGRESSION,
                LimitationSeverity.MAJOR,
                detail="regression(s) recorded post-merge",
                evidence_refs=["post_merge:regression_watch"])
    if post_merge.get("rollback_recommendation_status") not in (
            None, "no_rollback_needed", "monitor"):
        reg.add(LimitationCategory.UNRESOLVED_BLOCKER, LimitationSeverity.CRITICAL,
                detail=f"rollback watch: "
                       f"{post_merge.get('rollback_recommendation_status')}",
                evidence_refs=["post_merge:rollback_watch"])

    # Intake safety / coverage evidence.
    if int(intake.get("critical_safety_regression_count", 0) or 0) > 0:
        reg.add(LimitationCategory.WEAK_SAFETY_EVIDENCE,
                LimitationSeverity.CRITICAL,
                detail="critical safety regression in intake",
                evidence_refs=["intake:safety_regression"])
    if int(intake.get("coverage_gap_count", 0) or 0) > 0:
        reg.add(LimitationCategory.MISSING_EVIDENCE, LimitationSeverity.MAJOR,
                detail=f"{intake.get('coverage_gap_count')} coverage gap(s)",
                evidence_refs=["intake:coverage_matrix"])

    # Missing validation artifacts.
    if int(validation.get("validation_missing_count", 0) or 0) > 0:
        reg.add(LimitationCategory.MISSING_EVIDENCE, LimitationSeverity.MAJOR,
                detail="required validation artifact(s) missing",
                evidence_refs=["validation_summary"])

    # Missing snapshot artifacts (informational unless safety-relevant).
    missing = snapshot.get("missing", [])
    if "replication_report" in missing:
        reg.add(LimitationCategory.INSUFFICIENT_REPLICATION,
                LimitationSeverity.WARNING,
                detail="no replication report indexed",
                evidence_refs=["snapshot:replication_report"])
    if "falsification_report" in missing:
        reg.add(LimitationCategory.FAILED_FALSIFICATION,
                LimitationSeverity.WARNING,
                detail="no falsification report indexed (not run / not "
                       "supplied)",
                evidence_refs=["snapshot:falsification_report"])
    if "soak_dossier" in missing:
        reg.add(LimitationCategory.WEAK_SOAK_EVIDENCE, LimitationSeverity.WARNING,
                detail="no soak dossier indexed",
                evidence_refs=["snapshot:soak_dossier"])
    return reg
