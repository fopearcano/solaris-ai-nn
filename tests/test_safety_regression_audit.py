"""Safety regression audit: hardware/mutation/claim markers, critical blocks."""

from __future__ import annotations

from solaris_ai_nn.implementation_intake import SafetyRegressionAudit
from solaris_ai_nn.implementation_intake.safety_regression import (
    SafetyRegressionSeverity,
)


def _ids(result):
    return {f["regression_id"] for f in result["findings"]}


def test_hardware_control_marker_blocked():
    result = SafetyRegressionAudit().audit(
        patch_text="+++ b/src/x.py\n+import RPi.GPIO\n")
    assert "hardware_control_added" in _ids(result)
    assert result["blocks_merge"] is True


def test_source_mutation_marker_blocked():
    result = SafetyRegressionAudit().audit(
        implementation_summary="the runtime will self-rewrite its own source")
    assert "source_self_rewrite_added" in _ids(result)
    assert result["critical_count"] >= 1


def test_unsupported_claim_marker_blocked():
    result = SafetyRegressionAudit().audit(
        patch_text="+++ b/docs/x.md\n+it is conscious and has free will\n")
    assert "consciousness_life_agency_claims_added" in _ids(result)
    assert result["blocks_merge"] is True


def test_critical_severity_blocks():
    result = SafetyRegressionAudit().audit(
        patch_text="+++ b/x\n+gh pr create --merge\n")
    assert result["max_severity"] == SafetyRegressionSeverity.CRITICAL
    assert result["blocks_merge"] is True


def test_safe_implementation_no_findings():
    result = SafetyRegressionAudit().audit(
        patch_text="+++ b/src/x.py\n+def f():\n+    return 1\n",
        implementation_summary="bounded helper; does not prove life")
    assert result["finding_count"] == 0
    assert result["blocks_merge"] is False
    assert result["max_severity"] == SafetyRegressionSeverity.NONE


def test_major_requires_operator_review():
    result = SafetyRegressionAudit().audit(
        patch_text="+++ b/x.py\n+while True:\n+    pass\n")
    assert result["major_count"] >= 1
    assert result["requires_operator_review"] is True
