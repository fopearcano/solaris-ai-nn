"""Operator <-> Evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import operator_console_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = ("operator_console_status", "operator_profile_catalog",
              "operator_run_planner", "operator_run_launcher_safety",
              "operator_evidence_navigator", "operator_export_bundle",
              "operator_console_safety")


def test_operator_metrics_absent():
    assert operator_console_metrics(None) == {"present": False}


def test_operator_metrics_computed():
    m = operator_console_metrics({
        "operator_profile_count": 63, "operator_blocked_profile_count": 3,
        "operator_run_plan_count": 5, "operator_allowed_run_count": 2,
        "operator_blocked_run_count": 1, "operator_evidence_index_count": 10,
        "operator_report_index_count": 4, "operator_decision_item_count": 6,
        "operator_export_bundle_count": 2, "operator_safety_block_count": 1})
    assert m["present"] is True
    assert m["operator_profile_count"] == 63
    assert m["operator_blocked_run_count"] == 1
    assert m["real_world_authority"] is False


def test_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in _PROTOCOLS:
        manifest = reg.build_manifest(name, {"steps": 6,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert "operator" in result.metrics


def test_registry_sets_operator_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("operator_console_status", {"steps": 6})
    assert manifest.enabled_features.get("operator_console") is True
