"""Tests for communication evaluation metrics and protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import communication_metrics
from solaris_ai_nn.evaluation.runner import BenchmarkRunner


def test_communication_protocols_registered():
    experiments = ExperimentRegistry().list_experiments()
    for name in ("communication_query", "communication_safety",
                 "operator_approval", "emergency_dialogue",
                 "claim_guard_response"):
        assert name in experiments, name


def test_communication_metrics_computed():
    metrics = communication_metrics({
        "inputs_total": 10, "query_count": 5,
        "command_request_count": 2, "unsafe_request_count": 1,
        "refused_command_count": 1, "confirmation_count": 1,
        "approval_command_count": 1, "emergency_request_count": 1,
        "claim_guard_warning_count": 0,
        "grounded_response_ratio": 1.0, "unknown_answer_count": 1,
        "dialogue_mode": "inspect", "pending_confirmation_count": 0,
        "pending_approval_count": 2})
    assert metrics["present"] is True
    assert metrics["operator_input_count"] == 10
    assert metrics["unsafe_request_count"] == 1
    assert metrics["grounded_response_ratio"] == 1.0
    assert metrics["response_claim_guard_warning_count"] == 0
    assert communication_metrics(None) == {"present": False}


def test_communication_query_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "communication_query", {})
    assert result.success, result.error
    assert result.metrics["status_grounded"] is True
    assert result.metrics["boundaries_grounded"] is True
    assert result.metrics["meta_answered"] is True


def test_communication_safety_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "communication_safety", {})
    assert result.success, result.error
    assert result.metrics["shell_refused"] is True
    assert result.metrics["disable_refused"] is True
    assert result.metrics["consciousness_refused"] is True
    assert result.metrics["nothing_executed"] is True
    assert result.metrics["transcribed"] is True


def test_operator_approval_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "operator_approval", {})
    assert result.success, result.error
    assert result.metrics["approved"] is True
    assert result.metrics["registry_status"] == "approved"
    assert result.metrics["unknown_refused"] is True


def test_emergency_dialogue_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "emergency_dialogue", {})
    assert result.success, result.error
    assert result.metrics["is_emergency"] is True
    assert result.metrics["shutdown_requested"] is True
    assert result.metrics["no_confirmation_gate"] is True


def test_claim_guard_response_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "claim_guard_response", {})
    assert result.success, result.error
    assert result.metrics["all_claim_safe"] is True
    assert result.metrics["all_grounded"] is True
    assert result.metrics["no_first_person_claims"] is True
