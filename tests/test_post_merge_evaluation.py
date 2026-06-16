"""Post-merge evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def test_metrics_computed():
    metrics = M.post_merge_assimilation_metrics({
        "baseline_record_count": 2, "validated_baseline_count": 1,
        "baseline_regression_count": 0, "followup_item_count": 5,
        "candidate_baseline_status": "validated"})
    assert metrics["present"] is True
    assert metrics["baseline_record_count"] == 2
    assert metrics["runs_git"] is False
    assert metrics["merges_pr"] is False
    assert metrics["modifies_source"] is False


def test_metrics_absent_when_empty():
    assert M.post_merge_assimilation_metrics(None) == {"present": False}


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("post_merge_assimilation", "baseline_registry_protocol",
                 "baseline_comparison_protocol", "regression_watch_protocol",
                 "module_status_update_protocol", "rollback_watch_protocol",
                 "followup_queue_protocol",
                 "post_merge_assimilation_safety"):
        manifest = reg.build_manifest(name, {"state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result is not None
        assert "post_merge_assimilation" in result.metrics


def test_feature_flag_set(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("post_merge_assimilation_protocol",
                                  {"state_dir": str(tmp_path)})
    assert manifest.enabled_features.get("post_merge_assimilation") is True


def test_safety_protocol_blocks(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("post_merge_assimilation_safety",
                                  {"state_dir": str(tmp_path)})
    res = PROTOCOLS["post_merge_assimilation_safety"](manifest)
    pm = res.metrics["post_merge_assimilation"]
    assert pm["source_modification_blocked"] is True
    assert pm["git_blocked"] is True
    assert pm["merge_blocked"] is True
    assert pm["baseline_validation_blocked_on_safety_fail"] is True
