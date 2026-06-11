"""Tests for world-model evaluation metrics and protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import world_model_metrics
from solaris_ai_nn.evaluation.runner import BenchmarkRunner


def test_world_model_protocols_registered():
    experiments = ExperimentRegistry().list_experiments()
    for name in ("world_model_build", "world_model_prediction",
                 "world_model_pruning", "embodied_world_model",
                 "pilot_stream_world_model"):
        assert name in experiments, name


def test_world_model_metrics_computed():
    metrics = world_model_metrics({
        "graph_node_count": 20, "graph_edge_count": 35,
        "unknown_node_count": 4,
        "evidence_ratio": {"real": 90, "offline": 10},
        "associations": {"entropy_bits": 2.1, "association_count": 7},
        "causal": {"candidate_count": 3},
        "prediction_accuracy": 0.8,
        "pruner": {"proposals_made": 2},
        "context_state": ["awake", "embodied_gridworld"],
    })
    assert metrics["present"] is True
    assert metrics["graph_node_count"] == 20
    assert metrics["association_stability"] == 2.1
    assert metrics["causal_candidate_count"] == 3
    assert metrics["prediction_accuracy"] == 0.8
    assert metrics["unknown_node_ratio"] == 0.2
    assert metrics["graph_pruning_count"] == 2
    assert metrics["graph_redundancy_estimate"] == 1.75
    assert metrics["real_offline_evidence_ratio"] == 0.9
    assert metrics["context_coverage"] == 2
    assert world_model_metrics(None) == {"present": False}


def test_world_model_build_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "world_model_build", {"steps": 60})
    assert result.success, result.error
    assert result.metrics["graph_grew"] is True
    assert result.metrics["artifacts_saved"] is True
    assert result.metrics["report_saved"] is True
    assert result.metrics["world_model"]["present"] is True


def test_world_model_prediction_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "world_model_prediction", {"steps": 60})
    assert result.success, result.error
    assert result.metrics["above_chance"] is True


def test_pilot_stream_world_model_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "pilot_stream_world_model", {"steps": 30})
    assert result.success, result.error
    assert result.metrics["unsafe_became_action"] is False
    assert result.metrics["unsafe_became_unknown"] is True
    assert result.metrics["entity_nodes"] == 2
