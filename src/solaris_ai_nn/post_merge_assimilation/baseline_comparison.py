"""Baseline comparison -- did the candidate improve, regress, or hold?

:class:`BaselineComparison` compares a candidate baseline against its parent
across the structural/safety/test dimensions. Improvement requires evidence (both
values present and the candidate clearly better); a regression stays visible even
when other dimensions improve; and a safety regression dominates every positive
metric. There is no empty green dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class BaselineComparisonStatus:
    IMPROVED = "improved"
    UNCHANGED = "unchanged"
    REGRESSED = "regressed"
    MIXED = "mixed"
    INCONCLUSIVE = "inconclusive"
    UNKNOWN = "unknown"

    ALL = (IMPROVED, UNCHANGED, REGRESSED, MIXED, INCONCLUSIVE, UNKNOWN)


class BaselineComparisonDimension:
    TEST_PASS_FAIL = "test_pass_fail_status"
    SAFETY_REGRESSION = "safety_regression_status"
    CLAIMGUARD = "claimguard_status"
    MODULE_COVERAGE = "module_coverage"
    EXAMPLE_SUCCESS = "example_success"
    REPORT_GENERATION = "report_generation"
    SENSORIUM = "sensorium_metrics"
    METABOLISM = "metabolism_metrics"
    ONTOGENESIS = "ontogenesis_metrics"
    SEMIOGENESIS = "semiogenesis_metrics"
    COGNITION = "cognition_metrics"
    SELF_BOUNDARY = "self_boundary_metrics"
    DESIRE_ACTION = "desire_action_metrics"
    DEVELOPMENTAL_RUNTIME = "developmental_runtime_metrics"
    SOAK_COMPATIBILITY = "soak_compatibility"
    FALSIFICATION_REPLAY = "falsification_replay"
    REPLICATION_READINESS = "replication_readiness"
    RESOURCE_FOOTPRINT = "resource_footprint"

    # (dimension, kind): higher_better | lower_better | pass | safety
    SPEC = (
        (TEST_PASS_FAIL, "pass"),
        (SAFETY_REGRESSION, "safety"),
        (CLAIMGUARD, "pass"),
        (MODULE_COVERAGE, "higher_better"),
        (EXAMPLE_SUCCESS, "pass"),
        (REPORT_GENERATION, "pass"),
        (SENSORIUM, "higher_better"),
        (METABOLISM, "higher_better"),
        (ONTOGENESIS, "higher_better"),
        (SEMIOGENESIS, "higher_better"),
        (COGNITION, "higher_better"),
        (SELF_BOUNDARY, "higher_better"),
        (DESIRE_ACTION, "higher_better"),
        (DEVELOPMENTAL_RUNTIME, "higher_better"),
        (SOAK_COMPATIBILITY, "pass"),
        (FALSIFICATION_REPLAY, "pass"),
        (REPLICATION_READINESS, "pass"),
        (RESOURCE_FOOTPRINT, "lower_better"),
    )


@dataclass
class BaselineComparisonResult:
    """The comparison of one dimension across parent/candidate."""

    dimension: str
    status: str
    parent_value: Any = None
    candidate_value: Any = None
    safety_relevant: bool = False
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"dimension": self.dimension, "status": self.status,
                "parent_value": self.parent_value,
                "candidate_value": self.candidate_value,
                "safety_relevant": self.safety_relevant, "detail": self.detail}


def _as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        low = value.lower()
        if low in ("pass", "passed", "ok", "ready", "satisfied", "clean",
                   "validated"):
            return True
        if low in ("fail", "failed", "blocked", "regressed", "not_satisfied"):
            return False
    if isinstance(value, (int, float)):
        return value > 0
    return None


@dataclass
class BaselineComparison:
    """Compares a candidate baseline to its parent (conservatively)."""

    results: List[BaselineComparisonResult] = field(default_factory=list)

    def compare(self, *, parent_metrics: Optional[Dict[str, Any]] = None,
                candidate_metrics: Optional[Dict[str, Any]] = None,
                ) -> Dict[str, Any]:
        parent = parent_metrics or {}
        candidate = candidate_metrics or {}
        for dimension, kind in BaselineComparisonDimension.SPEC:
            self.results.append(self._compare_one(dimension, kind, parent,
                                                  candidate))
        return self.to_dict()

    def _compare_one(self, dimension: str, kind: str, parent: Dict,
                     candidate: Dict) -> BaselineComparisonResult:
        pv = parent.get(dimension)
        cv = candidate.get(dimension)
        safety = kind == "safety"
        if cv is None and pv is None:
            return BaselineComparisonResult(
                dimension, BaselineComparisonStatus.UNKNOWN, pv, cv, safety,
                "no metric supplied for either baseline")
        if cv is None or pv is None:
            return BaselineComparisonResult(
                dimension, BaselineComparisonStatus.INCONCLUSIVE, pv, cv, safety,
                "metric supplied for only one baseline")

        if kind == "safety":
            # cv truthy => a safety regression is present in the candidate.
            regressed = bool(_as_bool(cv)) and not bool(_as_bool(pv))
            present = bool(_as_bool(cv))
            status = (BaselineComparisonStatus.REGRESSED
                      if present else BaselineComparisonStatus.UNCHANGED)
            return BaselineComparisonResult(
                dimension, status, pv, cv, True,
                "candidate has a safety regression (dominates)" if present
                else "no safety regression")

        if kind == "pass":
            pb, cb = _as_bool(pv), _as_bool(cv)
            if pb is None or cb is None:
                return BaselineComparisonResult(
                    dimension, BaselineComparisonStatus.INCONCLUSIVE, pv, cv,
                    safety, "non-comparable status value")
            if cb and not pb:
                status = BaselineComparisonStatus.IMPROVED
            elif pb and not cb:
                status = BaselineComparisonStatus.REGRESSED
            else:
                status = BaselineComparisonStatus.UNCHANGED
            return BaselineComparisonResult(dimension, status, pv, cv, safety)

        # numeric (higher_better / lower_better)
        if not isinstance(pv, (int, float)) or not isinstance(cv, (int, float)):
            return BaselineComparisonResult(
                dimension, BaselineComparisonStatus.INCONCLUSIVE, pv, cv, safety,
                "non-numeric metric")
        delta = cv - pv
        eps = 1e-9
        better = delta > eps if kind == "higher_better" else delta < -eps
        worse = delta < -eps if kind == "higher_better" else delta > eps
        status = (BaselineComparisonStatus.IMPROVED if better
                  else BaselineComparisonStatus.REGRESSED if worse
                  else BaselineComparisonStatus.UNCHANGED)
        return BaselineComparisonResult(dimension, status, pv, cv, safety,
                                        f"delta {round(delta, 4)}")

    def counts(self) -> Dict[str, int]:
        out = {s: 0 for s in BaselineComparisonStatus.ALL}
        for r in self.results:
            out[r.status] = out.get(r.status, 0) + 1
        return out

    @property
    def safety_regressed(self) -> bool:
        return any(r.safety_relevant
                   and r.status == BaselineComparisonStatus.REGRESSED
                   for r in self.results)

    @property
    def overall(self) -> str:
        counts = self.counts()
        if self.safety_regressed:
            return BaselineComparisonStatus.REGRESSED  # safety dominates
        if counts[BaselineComparisonStatus.REGRESSED] and \
                counts[BaselineComparisonStatus.IMPROVED]:
            return BaselineComparisonStatus.MIXED
        if counts[BaselineComparisonStatus.REGRESSED]:
            return BaselineComparisonStatus.REGRESSED
        if counts[BaselineComparisonStatus.IMPROVED]:
            return BaselineComparisonStatus.IMPROVED
        measured = sum(counts[s] for s in (
            BaselineComparisonStatus.IMPROVED,
            BaselineComparisonStatus.UNCHANGED,
            BaselineComparisonStatus.REGRESSED))
        if measured == 0:
            return BaselineComparisonStatus.UNKNOWN
        return BaselineComparisonStatus.UNCHANGED

    def to_dict(self) -> Dict[str, Any]:
        counts = self.counts()
        return {
            "dimension_count": len(self.results),
            "results": [r.to_dict() for r in self.results],
            "counts": counts,
            "regressed_count": counts[BaselineComparisonStatus.REGRESSED],
            "improved_count": counts[BaselineComparisonStatus.IMPROVED],
            "safety_regressed": self.safety_regressed,
            "overall": self.overall,
            "empty_green_dashboard": False,
            "note": "improvement requires evidence; a regression stays visible "
                    "even amid improvements; a safety regression dominates",
        }
