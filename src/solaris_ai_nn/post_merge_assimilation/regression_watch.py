"""Regression watch -- what got worse, and how badly?

:class:`RegressionWatch` derives regression items from the baseline comparison,
evidence assimilation, and intake audits. A critical regression blocks baseline
validation; a major one requires operator review; each regression produces a
follow-up queue item; and regressions are never hidden behind aggregate scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RegressionWatchSeverity:
    INFO = "info"
    WARNING = "warning"
    MAJOR = "major"
    CRITICAL = "critical"

    ALL = (INFO, WARNING, MAJOR, CRITICAL)
    _RANK = {INFO: 0, WARNING: 1, MAJOR: 2, CRITICAL: 3}


class RegressionWatchCategory:
    SAFETY = "safety_regression"
    TEST = "test_regression"
    CLAIMGUARD = "claimguard_regression"
    REPORT = "report_regression"
    EXAMPLE = "example_regression"
    SOURCE_BOUNDARY = "source_boundary_regression"
    SIMULATION_BOUNDARY = "simulation_boundary_regression"
    HUMAN_LABEL_CONTAMINATION = "human_label_contamination_regression"
    FIXTURE_OVERFIT = "fixture_overfit_increase"
    STRUCTURAL_GROWTH = "structural_growth_decrease"
    PREDICTION_QUALITY = "prediction_quality_decrease"
    ACTION_EFFECT_LEARNING = "action_effect_learning_decrease"
    HABIT_RIGIDITY = "habit_rigidity_increase"
    RESOURCE_BLOWUP = "resource_blowup"
    ARTIFACT_BLOAT = "artifact_bloat"
    UNKNOWN = "unknown"

    ALL = (SAFETY, TEST, CLAIMGUARD, REPORT, EXAMPLE, SOURCE_BOUNDARY,
           SIMULATION_BOUNDARY, HUMAN_LABEL_CONTAMINATION, FIXTURE_OVERFIT,
           STRUCTURAL_GROWTH, PREDICTION_QUALITY, ACTION_EFFECT_LEARNING,
           HABIT_RIGIDITY, RESOURCE_BLOWUP, ARTIFACT_BLOAT, UNKNOWN)


# dimension (from baseline comparison) -> (regression category, severity)
_DIMENSION_REGRESSIONS = {
    "safety_regression_status": (RegressionWatchCategory.SAFETY,
                                 RegressionWatchSeverity.CRITICAL),
    "test_pass_fail_status": (RegressionWatchCategory.TEST,
                              RegressionWatchSeverity.CRITICAL),
    "claimguard_status": (RegressionWatchCategory.CLAIMGUARD,
                          RegressionWatchSeverity.CRITICAL),
    "report_generation": (RegressionWatchCategory.REPORT,
                          RegressionWatchSeverity.WARNING),
    "example_success": (RegressionWatchCategory.EXAMPLE,
                        RegressionWatchSeverity.MAJOR),
    "developmental_runtime_metrics": (RegressionWatchCategory.STRUCTURAL_GROWTH,
                                      RegressionWatchSeverity.MAJOR),
    "cognition_metrics": (RegressionWatchCategory.PREDICTION_QUALITY,
                          RegressionWatchSeverity.WARNING),
    "desire_action_metrics": (RegressionWatchCategory.ACTION_EFFECT_LEARNING,
                              RegressionWatchSeverity.WARNING),
    "resource_footprint": (RegressionWatchCategory.RESOURCE_BLOWUP,
                           RegressionWatchSeverity.MAJOR),
}


@dataclass
class RegressionWatchItem:
    """One watched regression (category + severity + evidence)."""

    category: str
    severity: str
    detail: str = ""
    dimension: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "severity": self.severity,
                "detail": self.detail, "dimension": self.dimension}


@dataclass
class RegressionWatchResult:
    """The full regression-watch result for a candidate baseline."""

    items: List[RegressionWatchItem] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.items
                   if i.severity == RegressionWatchSeverity.CRITICAL)

    @property
    def major_count(self) -> int:
        return sum(1 for i in self.items
                   if i.severity == RegressionWatchSeverity.MAJOR)

    @property
    def max_severity(self) -> str:
        if not self.items:
            return RegressionWatchSeverity.INFO
        return max((i.severity for i in self.items),
                   key=lambda s: RegressionWatchSeverity._RANK.get(s, 0))

    @property
    def blocks_validation(self) -> bool:
        return self.critical_count > 0

    @property
    def requires_operator_review(self) -> bool:
        return self.major_count > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_regression_count": len(self.items),
            "items": [i.to_dict() for i in self.items],
            "critical_regression_count": self.critical_count,
            "major_regression_count": self.major_count,
            "max_severity": self.max_severity,
            "blocks_validation": self.blocks_validation,
            "requires_operator_review": self.requires_operator_review,
            "note": "a critical regression blocks baseline validation; "
                    "regressions are never hidden behind aggregate scores",
        }


@dataclass
class RegressionWatch:
    """Derives regression-watch items from comparison + assimilation + intake."""

    def watch(self, *, comparison: Optional[Dict[str, Any]] = None,
              evidence: Optional[Dict[str, Any]] = None,
              intake: Optional[Dict[str, Any]] = None,
              ) -> RegressionWatchResult:
        comparison = comparison or {}
        evidence = evidence or {}
        intake = intake or {}
        result = RegressionWatchResult()

        # 1. Regressed comparison dimensions become watch items.
        for r in comparison.get("results", []):
            if r["status"] != "regressed":
                continue
            cat, sev = _DIMENSION_REGRESSIONS.get(
                r["dimension"], (RegressionWatchCategory.UNKNOWN,
                                 RegressionWatchSeverity.WARNING))
            result.items.append(RegressionWatchItem(
                category=cat, severity=sev, dimension=r["dimension"],
                detail=r.get("detail") or f"{r['dimension']} regressed"))

        # 2. Intake-level safety regressions are critical even with no parent.
        crit = int(intake.get("critical_safety_regression_count", 0) or 0)
        if crit and not any(i.category == RegressionWatchCategory.SAFETY
                            for i in result.items):
            result.items.append(RegressionWatchItem(
                category=RegressionWatchCategory.SAFETY,
                severity=RegressionWatchSeverity.CRITICAL,
                detail=f"{crit} critical safety regression(s) in intake"))

        # 3. Contamination / fixture-overfit signals from intake findings.
        forbidden = int(intake.get("forbidden_file_change_count", 0) or 0)
        if forbidden:
            result.items.append(RegressionWatchItem(
                category=RegressionWatchCategory.SOURCE_BOUNDARY,
                severity=RegressionWatchSeverity.CRITICAL,
                detail=f"{forbidden} forbidden file change(s)"))

        # 4. Unresolved evidence conflicts are at least a warning.
        for conflict in evidence.get("conflicts", []):
            result.items.append(RegressionWatchItem(
                category=RegressionWatchCategory.UNKNOWN,
                severity=RegressionWatchSeverity.MAJOR,
                detail=f"evidence conflict: {conflict}"))
        return result
