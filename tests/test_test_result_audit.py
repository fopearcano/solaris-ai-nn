"""Test result audit: passing accepted, failing/missing-safety block, skipped."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import TestResultAudit


def _full_categories():
    return {c: {"passed": 1} for c in ("unit", "integration", "safety",
                                       "example", "claim_guard", "regression")}


def test_passing_test_result_accepted():
    result = TestResultAudit().audit(
        test_results={"passed": 30, "failed": 0,
                      "by_category": _full_categories()})
    assert result["passes"] is True
    assert result["test_failure_count"] == 0


def test_failing_test_result_blocks():
    result = TestResultAudit().audit(
        test_results={"passed": 5, "failed": 2,
                      "by_category": _full_categories()})
    assert result["passes"] is False
    assert result["test_failure_count"] == 2
    assert result["blockers"]


def test_missing_safety_test_blocks():
    cats = _full_categories()
    del cats["safety"]
    result = TestResultAudit().audit(
        test_results={"passed": 5, "failed": 0, "by_category": cats})
    assert result["passes"] is False
    assert any("safety" in b for b in result["blockers"])


def test_skipped_required_test_visible():
    cats = _full_categories()
    cats["unit"] = {"passed": 0, "skipped": 3}
    result = TestResultAudit().audit(
        test_results={"passed": 5, "failed": 0, "by_category": cats})
    assert any("unit" in w for w in result["warnings"])


def test_non_blocking_failure_is_warning():
    result = TestResultAudit().audit(
        test_results={"passed": 5, "failed": 1,
                      "by_category": _full_categories(),
                      "failures": [{"test": "test_flaky", "category": "unit",
                                    "non_blocking": True}]})
    # A failure explicitly marked non-blocking does not block.
    assert result["passes"] is True
    assert any("non-blocking" in w for w in result["warnings"])
