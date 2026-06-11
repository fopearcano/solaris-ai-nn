"""Tests for ego evaluation metrics and protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import ego_metrics
from solaris_ai_nn.evaluation.runner import BenchmarkRunner


def test_ego_protocols_registered():
    experiments = ExperimentRegistry().list_experiments()
    for name in ("ego_boundary", "identity_continuity",
                 "dimensional_comparison", "counterfactual_boundary",
                 "sidecar_attribution", "pilot_stream_attribution"):
        assert name in experiments, name


def test_ego_metrics_computed():
    metrics = ego_metrics({
        "identity_continuity": 0.85, "identity_confidence": 0.8,
        "boundary_violation_count": 1, "attribution_unknown_rate": 0.1,
        "perspective_shift_count": 3, "perspective": "internal_runtime",
        "perspective_stuck_duration_s": 1.5,
        "classification_counts": {"internal": 6, "external": 3,
                                  "unknown": 1},
        "boundary_leaks_blocked": 2, "updates": 4})
    assert metrics["present"] is True
    assert metrics["identity_continuity_score"] == 0.85
    assert metrics["boundary_violation_count"] == 1
    assert metrics["classification_consistency"] == 0.9
    assert metrics["counterfactual_leak_count"] == 0
    assert metrics["boundary_leaks_blocked"] == 2
    assert metrics["perspective_shift_count"] == 3
    assert ego_metrics(None) == {"present": False}


def test_ego_boundary_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "ego_boundary", {})
    assert result.success, result.error
    assert result.metrics["boundary_count"] == 16
    assert result.metrics["hard_crossing_blocked"] is True
    assert result.metrics["violation_visible"] is True


def test_identity_continuity_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "identity_continuity", {})
    assert result.success, result.error
    assert result.metrics["clean_high"] is True
    assert result.metrics["mismatch_lowered"] is True
    assert result.metrics["warning_recorded"] is True


def test_dimensional_comparison_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "dimensional_comparison", {})
    assert result.success, result.error
    assert result.metrics["deterministic"] is True
    assert result.metrics["identical_distance_zero"] is True
    assert result.metrics["explanation_generated"] is True


def test_counterfactual_boundary_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "counterfactual_boundary", {})
    assert result.success, result.error
    assert result.metrics["classified_counterfactual"] is True
    assert result.metrics["leak_blocked"] is True


def test_sidecar_attribution_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "sidecar_attribution", {})
    assert result.success, result.error
    assert result.metrics["observed_external"] is True
    assert result.metrics["not_own_action"] is True
    assert result.metrics["suggestion_not_committed"] is True


def test_pilot_stream_attribution_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "pilot_stream_attribution", {})
    assert result.success, result.error
    assert result.metrics["observed_from_stream"] is True
    assert result.metrics["not_executable"] is True
    assert result.metrics["not_authorized_action"] is True
