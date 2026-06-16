"""Baseline comparison: statuses, safety dominance, no empty green dashboard."""

from __future__ import annotations

from solaris_ai_nn.post_merge_assimilation import (
    BaselineComparison,
    BaselineComparisonStatus,
)


def _by_dim(result):
    return {r["dimension"]: r["status"] for r in result["results"]}


def test_improved_regressed_inconclusive_statuses():
    result = BaselineComparison().compare(
        parent_metrics={"sensorium_metrics": 0.5, "module_coverage": 0.8,
                        "cognition_metrics": 0.4},
        candidate_metrics={"sensorium_metrics": 0.6,    # improved
                          "module_coverage": 0.7,        # regressed
                          # cognition only in parent -> inconclusive
                          })
    dims = _by_dim(result)
    assert dims["sensorium_metrics"] == BaselineComparisonStatus.IMPROVED
    assert dims["module_coverage"] == BaselineComparisonStatus.REGRESSED
    assert dims["cognition_metrics"] == BaselineComparisonStatus.INCONCLUSIVE


def test_safety_regression_dominates():
    result = BaselineComparison().compare(
        parent_metrics={"sensorium_metrics": 0.5,
                        "safety_regression_status": False},
        candidate_metrics={"sensorium_metrics": 0.99,   # big improvement
                          "safety_regression_status": True})  # regression
    assert result["safety_regressed"] is True
    assert result["overall"] == BaselineComparisonStatus.REGRESSED


def test_no_empty_green_dashboard():
    result = BaselineComparison().compare(parent_metrics={},
                                          candidate_metrics={})
    assert result["empty_green_dashboard"] is False
    assert result["overall"] == BaselineComparisonStatus.UNKNOWN


def test_improvement_requires_evidence():
    # A dimension present only in the candidate is inconclusive, not improved.
    result = BaselineComparison().compare(
        parent_metrics={}, candidate_metrics={"sensorium_metrics": 0.9})
    dims = _by_dim(result)
    assert dims["sensorium_metrics"] == BaselineComparisonStatus.INCONCLUSIVE
    assert result["improved_count"] == 0


def test_mixed_when_both_improve_and_regress():
    result = BaselineComparison().compare(
        parent_metrics={"sensorium_metrics": 0.5, "module_coverage": 0.8,
                        "safety_regression_status": False},
        candidate_metrics={"sensorium_metrics": 0.6, "module_coverage": 0.7,
                          "safety_regression_status": False})
    assert result["overall"] == BaselineComparisonStatus.MIXED
