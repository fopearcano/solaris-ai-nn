"""Tests for developmental evaluation metrics and protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import developmental_metrics
from solaris_ai_nn.evaluation.runner import BenchmarkRunner


def test_developmental_protocols_registered():
    experiments = ExperimentRegistry().list_experiments()
    for name in ("developmental_short_simulation",
                 "memory_layer_compression", "milestone_detection",
                 "drift_monitor", "phase_transition_detection",
                 "autobiographical_memory"):
        assert name in experiments, name


def test_developmental_metrics_computed():
    metrics = developmental_metrics({
        "structural_change_score": 0.25,
        "developmental_stability_score": 0.9,
        "memory_layers": {"compression_ratio": 0.15},
        "identity_continuity": 0.95, "stagnation_windows": 2,
        "drift_velocity": 0.03, "milestone_rate": 0.01,
        "fossil_memory_rate": 0.005, "milestone_count": 7,
        "fossil_memory_count": 5, "epoch_transition_count": 3,
        "current_epoch": "consolidation_dominant",
        "developmental_age_hours": 200.0,
        "growth_status": "consolidation",
        "drift_status": "healthy_slow"})
    assert metrics["present"] is True
    assert metrics["structural_change_score"] == 0.25
    assert metrics["memory_compression_ratio"] == 0.15
    assert metrics["stagnation_duration"] == 2
    assert metrics["epoch_transition_count"] == 3
    assert "consciousness_score" not in metrics
    assert "life_score" not in metrics
    assert developmental_metrics(None) == {"present": False}


def test_short_simulation_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "developmental_short_simulation", {})
    assert result.success, result.error
    assert result.metrics["completed"] is True
    assert result.metrics["state_saved"] is True
    assert result.metrics["simulated"] is True
    assert result.metrics["milestones"] >= 1


def test_memory_compression_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "memory_layer_compression", {})
    assert result.success, result.error
    assert result.metrics["compressed"] is True
    assert result.metrics["evidence_summary_present"] is True
    assert result.metrics["important_preserved"] is True
    assert result.metrics["movements_audited"] is True


def test_milestone_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "milestone_detection", {})
    assert result.success, result.error
    assert result.metrics["fired_once"] is True
    assert result.metrics["evidence_present"] is True
    assert result.metrics["fossil_candidates"] is True


def test_drift_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "drift_monitor", {})
    assert result.success, result.error
    assert result.metrics["slow_ok"] is True
    assert result.metrics["fast_warns"] is True
    assert result.metrics["inert_warns"] is True


def test_phase_transition_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "phase_transition_detection", {})
    assert result.success, result.error
    assert result.metrics["before_after_present"] is True
    assert result.metrics["confidence_exposed"] is True
    assert result.metrics["hypothesis_note"] is True


def test_autobiographical_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "autobiographical_memory", {})
    assert result.success, result.error
    assert result.metrics["first_person_rejected"] is True
    assert result.metrics["simulated_marked"] is True
    assert result.metrics["real_marked"] is True
