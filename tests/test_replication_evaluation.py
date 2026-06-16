"""Replication evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS


def test_metrics_computed():
    metrics = M.developmental_replication_metrics({
        "registered_run_count": 3, "aligned_run_pair_count": 3,
        "replicated_claim_count": 19, "falsified_claim_count": 2,
        "structural_similarity_mean": 0.5})
    assert metrics["present"] is True
    assert metrics["registered_run_count"] == 3
    assert metrics["is_biological_ancestry"] is False
    assert metrics["is_consciousness_or_personhood"] is False


def test_metrics_absent_when_empty():
    assert M.developmental_replication_metrics(None) == {"present": False}


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("developmental_replication", "run_registry_evaluation",
                 "lineage_evaluation", "cross_run_alignment_protocol",
                 "structural_similarity_protocol", "divergence_analysis_protocol",
                 "environmental_dependency_protocol", "falsification_lab_protocol",
                 "replication_matrix_protocol",
                 "developmental_replication_safety"):
        manifest = reg.build_manifest(name, {"state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result is not None
        assert "developmental_replication" in result.metrics


def test_feature_flag_set(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("developmental_replication_protocol",
                                  {"state_dir": str(tmp_path)})
    assert manifest.enabled_features.get("developmental_replication") is True


def test_safety_protocol_blocks(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("developmental_replication_safety",
                                  {"state_dir": str(tmp_path)})
    res = PROTOCOLS["developmental_replication_safety"](manifest)
    dr = res.metrics["developmental_replication"]
    assert dr["unbounded_blocked"] is True
    assert dr["ancestry_claim_blocked"] is True
    assert dr["life_claim_blocked"] is True
