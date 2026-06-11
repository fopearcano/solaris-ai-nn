"""Tests for homeostasis evaluation metrics and protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import homeostasis_metrics
from solaris_ai_nn.evaluation.runner import BenchmarkRunner


def test_homeostasis_protocols_registered():
    experiments = ExperimentRegistry().list_experiments()
    for name in ("homeostasis_energy", "homeostasis_danger_reward",
                 "need_conflict", "auto_determination_continuity",
                 "homeostasis_latent"):
        assert name in experiments, name


def test_homeostasis_metrics_computed():
    traces = [
        {"dominant_need": "restore_energy", "tension": 0.1},
        {"dominant_need": "restore_energy", "tension": 0.2},
        {"dominant_need": "avoid_danger", "tension": 0.4},
        {"dominant_need": "restore_energy", "tension": 0.5},
    ]
    metrics = homeostasis_metrics({
        "updates": 4, "conflict_count": 2, "suppressed_desire_count": 3,
        "valence_trend": "falling", "current_valence": -0.2,
        "being_pressure": 0.7, "not_being_pressure": 0.3,
        "shutdown_recommendations": 1, "dominant_need": "restore_energy",
        "dominant_drive": "energy_drive", "best_desire": "rest"}, traces)
    assert metrics["present"] is True
    assert metrics["dominant_need_stability"] == 0.75
    assert metrics["need_volatility"] == round(2 / 3, 4)
    assert metrics["desire_suppression_rate"] == 0.75
    assert metrics["auto_determination_tension_trend"] > 0  # rising
    assert metrics["safe_shutdown_recommendation_count"] == 1
    assert homeostasis_metrics(None) == {"present": False}


def test_energy_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "homeostasis_energy", {"steps": 20})
    assert result.success, result.error
    assert result.metrics["healthy_had_energy_need"] is False
    assert result.metrics["depleted_dominant"] == "restore_energy"
    assert result.metrics["rest_suggested"] is True


def test_danger_reward_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "homeostasis_danger_reward", {"steps": 20})
    assert result.success, result.error
    assert result.metrics["avoid_danger_active"] is True
    assert result.metrics["approach_reward_blocked"] is True
    assert result.metrics["block_reason_recorded"] is True


def test_auto_determination_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "auto_determination_continuity", {"steps": 20})
    assert result.success, result.error
    assert result.metrics["being_dropped"] is True
    assert result.metrics["shutdown_or_review_recommended"] is True
