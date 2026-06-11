"""Tests for executive evaluation metrics and protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import executive_metrics
from solaris_ai_nn.evaluation.runner import BenchmarkRunner


def test_executive_protocols_registered():
    experiments = ExperimentRegistry().list_experiments()
    for name in ("executive_arbitration", "executive_inhibition",
                 "executive_prospection", "short_plan_gridworld",
                 "executive_emergency_mode", "executive_sidecar_observe"):
        assert name in experiments, name


def test_executive_metrics_computed():
    rows = [
        {"selected": "rest", "scores": [{"total": 1.2}]},
        {"selected": "rest", "scores": [{"total": 1.0}]},
        {"selected": "look", "scores": [{"total": 1.1}]},
    ]
    metrics = executive_metrics({
        "decisions": 3, "desire_queue_length": 2, "candidate_count": 4,
        "inhibited_candidate_count": 6, "no_safe_action_count": 1,
        "selected_plan_length": 2, "plans_rejected": 1,
        "fallback_total": 1, "forced_emergency_total": 0,
        "last_prospection_confidence": 0.4}, rows)
    assert metrics["present"] is True
    assert metrics["inhibition_count"] == 6
    assert metrics["inhibition_rate"] == 2.0
    assert metrics["selected_action_diversity"] == round(2 / 3, 4)
    assert metrics["arbitration_score_stability"] is not None
    assert metrics["safety_override_count"] == 0  # no override path exists
    assert executive_metrics(None) == {"present": False}


def test_arbitration_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "executive_arbitration", {})
    assert result.success, result.error
    assert result.metrics["components_visible"] is True
    assert result.metrics["blocked_never_selected"] is True


def test_inhibition_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "executive_inhibition", {})
    assert result.success, result.error
    assert result.metrics["all_families_fired"] is True
    assert result.metrics["reasons_recorded"] is True


def test_prospection_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "executive_prospection", {})
    assert result.success, result.error
    assert result.metrics["blind_is_unknown"] is True
    assert result.metrics["marked_simulated"] is True


def test_short_plan_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "short_plan_gridworld", {})
    assert result.success, result.error
    assert result.metrics["plan_length_ok"] is True
    assert result.metrics["long_plan_refused"] is True
    assert result.metrics["suggestion_only"] is True


def test_emergency_mode_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "executive_emergency_mode", {})
    assert result.success, result.error
    assert result.metrics["mode"] == "emergency"
    assert result.metrics["selected_is_safe_fallback"] is True
    assert result.metrics["cannot_leave_emergency"] is True


def test_sidecar_observe_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "executive_sidecar_observe", {})
    assert result.success, result.error
    assert result.metrics["committed_always_false"] is True
    assert result.metrics["publish_blocked_without_approval"] is True
    assert result.metrics["publish_allowed_with_approval"] is True
