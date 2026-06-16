"""Intake evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def test_metrics_computed():
    metrics = M.implementation_intake_metrics({
        "implementation_artifact_count": 9, "test_failure_count": 0,
        "safety_regression_count": 0, "coverage_gap_count": 0,
        "merge_recommendation_status": "recommend_merge"})
    assert metrics["present"] is True
    assert metrics["implementation_artifact_count"] == 9
    assert metrics["modifies_source"] is False
    assert metrics["merges_pr"] is False
    assert metrics["calls_github"] is False


def test_metrics_absent_when_empty():
    assert M.implementation_intake_metrics(None) == {"present": False}


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("implementation_intake", "diff_audit_protocol",
                 "spec_compliance_protocol", "test_result_audit_protocol",
                 "safety_regression_protocol", "coverage_matrix_evaluation",
                 "merge_recommendation_protocol",
                 "implementation_intake_safety"):
        manifest = reg.build_manifest(name, {"state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result is not None
        assert "implementation_intake" in result.metrics


def test_feature_flag_set(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("implementation_intake_protocol",
                                  {"state_dir": str(tmp_path)})
    assert manifest.enabled_features.get("implementation_intake") is True


def test_safety_protocol_blocks(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("implementation_intake_safety",
                                  {"state_dir": str(tmp_path)})
    res = PROTOCOLS["implementation_intake_safety"](manifest)
    ii = res.metrics["implementation_intake"]
    assert ii["source_modification_blocked"] is True
    assert ii["merge_blocked"] is True
    assert ii["github_blocked"] is True
    assert ii["agent_blocked"] is True
