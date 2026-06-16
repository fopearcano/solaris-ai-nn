"""Research baseline evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def test_metrics_computed():
    metrics = M.research_baseline_metrics({
        "research_baseline_version_count": 1, "capability_count": 22,
        "limitation_count": 1, "comparison_anchor_count": 12,
        "baseline_status": "validated"})
    assert metrics["present"] is True
    assert metrics["capability_count"] == 22
    assert metrics["is_git_tag"] is False
    assert metrics["is_github_release"] is False
    assert metrics["is_product_release"] is False


def test_metrics_absent_when_empty():
    assert M.research_baseline_metrics(None) == {"present": False}


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("research_baseline", "baseline_version_protocol",
                 "snapshot_manifest_protocol", "repro_bundle_protocol",
                 "capability_map_protocol", "limitation_registry_protocol",
                 "validation_summary_protocol", "comparison_anchor_protocol",
                 "roadmap_reset_protocol", "research_baseline_safety"):
        manifest = reg.build_manifest(name, {"state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result is not None
        assert "research_baseline" in result.metrics


def test_feature_flag_set(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("research_baseline_protocol",
                                  {"state_dir": str(tmp_path)})
    assert manifest.enabled_features.get("research_baseline") is True


def test_safety_protocol_blocks(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("research_baseline_safety",
                                  {"state_dir": str(tmp_path)})
    res = PROTOCOLS["research_baseline_safety"](manifest)
    rb = res.metrics["research_baseline"]
    assert rb["git_tag_blocked"] is True
    assert rb["release_blocked"] is True
    assert rb["source_modification_blocked"] is True
    assert rb["validated_blocked_on_safety_fail"] is True
