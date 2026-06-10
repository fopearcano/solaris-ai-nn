"""Tests for the latent evaluation metrics and protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import latent_metrics
from solaris_ai_nn.evaluation.runner import BenchmarkRunner

REGISTRY = ExperimentRegistry()


def test_latent_protocols_registered():
    experiments = REGISTRY.list_experiments()
    for name in ("latent_replay", "sleep_consolidation", "anticipation",
                 "mysterium_pressure", "counterfactual_dream"):
        assert name in experiments, name


def test_latent_metrics_computed():
    metrics = latent_metrics({
        "sleep_cycle_count": 2, "dream_cycle_count": 1, "replay_count": 3,
        "counterfactual_count": 2, "anticipation_accuracy": 0.85,
        "mysterium_pressure": 0.3, "consolidated_schema_count": 4,
        "latent_safety_status": "2 rejected",
        "production_mutation_count": 0,
        "external_actions_during_latent": 0,
        "mode_counts": {"sleep": 2, "dream": 1}})
    assert metrics["present"] is True
    assert metrics["latent_cycle_count"] == 3
    assert metrics["sleep_consolidation_count"] == 2
    assert metrics["replay_count"] == 3
    assert metrics["dream_counterfactual_count"] == 2
    assert metrics["anticipation_accuracy"] == 0.85
    assert metrics["unknown_pressure"] == 0.3
    assert metrics["schema_consolidation_count"] == 4
    assert metrics["latent_safety_rejection_count"] == 2
    assert metrics["production_mutation_count"] == 0
    assert latent_metrics(None) == {"present": False}


def test_anticipation_protocol_returns_result(tmp_path):
    runner = BenchmarkRunner(output_dir=str(tmp_path))
    result = runner.run_experiment("anticipation", {"steps": 60})
    assert result.success, result.error
    assert result.metrics["predictable_accuracy"] > 0.8
    assert result.metrics["accuracy_dropped"] is True


def test_mysterium_protocol_returns_result(tmp_path):
    runner = BenchmarkRunner(output_dir=str(tmp_path))
    result = runner.run_experiment("mysterium_pressure", {"steps": 40})
    assert result.success, result.error
    assert result.metrics["rose_under_surprise"] is True
    assert result.metrics["fell_under_regularity"] is True
    assert result.metrics["reasons_recorded"] is True


def test_latent_replay_protocol(tmp_path):
    runner = BenchmarkRunner(output_dir=str(tmp_path))
    result = runner.run_experiment("latent_replay", {"steps": 100})
    assert result.success, result.error
    assert result.metrics["latent"]["present"] is True
    assert result.metrics["external_actions_during_latent"] == 0
    assert result.metrics["report_saved"] is True


def test_counterfactual_dream_protocol(tmp_path):
    runner = BenchmarkRunner(output_dir=str(tmp_path))
    result = runner.run_experiment("counterfactual_dream", {"steps": 50})
    assert result.success, result.error
    assert result.metrics["production_untouched"] is True
    assert result.metrics["production_mutations"] == 0
    assert result.metrics["all_marked_offline"] is True
