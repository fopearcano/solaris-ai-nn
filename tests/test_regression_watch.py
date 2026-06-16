"""Regression watch: critical blocks, major needs review, follow-up created."""

from __future__ import annotations

from solaris_ai_nn.post_merge_assimilation import (
    BaselineComparison,
    RegressionWatch,
    RegressionWatchSeverity,
    build_followup_queue,
)


def _comparison(candidate):
    return BaselineComparison().compare(
        parent_metrics={"safety_regression_status": False,
                        "test_pass_fail_status": "pass",
                        "example_success": "pass",
                        "developmental_runtime_metrics": 0.5},
        candidate_metrics=candidate)


def test_critical_regression_blocks_validation():
    comp = _comparison({"safety_regression_status": True,
                       "test_pass_fail_status": "pass"})
    result = RegressionWatch().watch(comparison=comp).to_dict()
    assert result["critical_regression_count"] >= 1
    assert result["blocks_validation"] is True


def test_major_regression_requires_operator_review():
    comp = _comparison({"example_success": "fail",
                       "safety_regression_status": False,
                       "test_pass_fail_status": "pass"})
    result = RegressionWatch().watch(comparison=comp).to_dict()
    assert result["major_regression_count"] >= 1
    assert result["requires_operator_review"] is True
    assert result["max_severity"] in (RegressionWatchSeverity.MAJOR,
                                      RegressionWatchSeverity.CRITICAL)


def test_regression_followup_created():
    comp = _comparison({"safety_regression_status": True})
    regression = RegressionWatch().watch(comparison=comp).to_dict()
    queue = build_followup_queue(
        validation={"missing_required": []}, regression=regression,
        module_status={}, rollback={"recommendation": "rollback_recommended"},
        baseline_validated=False).to_dict()
    item_types = {i["item_type"] for i in queue["items"]}
    assert "monitor_regression" in item_types


def test_intake_safety_regression_is_critical_without_parent():
    result = RegressionWatch().watch(
        comparison={}, intake={"critical_safety_regression_count": 1}).to_dict()
    assert result["critical_regression_count"] >= 1
