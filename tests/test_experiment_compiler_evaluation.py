"""Compiler evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def test_metrics_computed():
    metrics = M.experiment_compiler_metrics({
        "compiler_input_source_count": 12, "compiled_spec_count": 4,
        "ready_spec_count": 2, "blocked_spec_count": 2,
        "prompt_pack_count": 2, "safety_gate_failure_count": 0})
    assert metrics["present"] is True
    assert metrics["compiled_spec_count"] == 4
    assert metrics["modifies_source"] is False
    assert metrics["creates_branch"] is False
    assert metrics["runs_external_agent"] is False


def test_metrics_absent_when_empty():
    assert M.experiment_compiler_metrics(None) == {"present": False}


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("experiment_compiler", "compiled_spec_evaluation",
                 "prompt_pack_generation_protocol",
                 "branch_spec_generation_protocol", "test_matrix_protocol",
                 "safety_gate_protocol", "operator_review_packet_protocol",
                 "validation_plan_protocol", "experiment_compiler_safety"):
        manifest = reg.build_manifest(name, {"state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result is not None
        assert "experiment_compiler" in result.metrics


def test_feature_flag_set(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("experiment_compiler_protocol",
                                  {"state_dir": str(tmp_path)})
    assert manifest.enabled_features.get("experiment_compiler") is True


def test_safety_protocol_blocks(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("experiment_compiler_safety",
                                  {"state_dir": str(tmp_path)})
    res = PROTOCOLS["experiment_compiler_safety"](manifest)
    ec = res.metrics["experiment_compiler"]
    assert ec["source_modification_blocked"] is True
    assert ec["branch_creation_blocked"] is True
    assert ec["pr_creation_blocked"] is True
    assert ec["external_agent_blocked"] is True
