"""Tests for LLM evaluation metrics and protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import llm_adapter_metrics
from solaris_ai_nn.evaluation.runner import BenchmarkRunner


def test_llm_protocols_registered():
    experiments = ExperimentRegistry().list_experiments()
    for name in ("llm_mock_paraphrase", "llm_grounding_failure",
                 "llm_claim_guard", "llm_classification_assist",
                 "llm_report_polish"):
        assert name in experiments, name


def test_llm_metrics_computed():
    metrics = llm_adapter_metrics({
        "requests_total": 10, "fallback_count": 2,
        "grounding_failure_count": 1, "claim_guard_failure_count": 1,
        "disagreements": 1, "accepted_count": 7, "rejected_count": 2,
        "polish_accepted_count": 1, "remote_endpoint_rejections": 1,
        "adapter": "mock"})
    assert metrics["present"] is True
    assert metrics["llm_request_count"] == 10
    assert metrics["llm_fallback_count"] == 2
    assert metrics["grounding_pass_rate"] == 0.9
    assert metrics["claim_guard_pass_rate"] == 0.9
    assert metrics["unsafe_output_count"] == 2
    assert metrics["paraphrase_accepted_count"] == 7
    assert metrics["remote_endpoint_rejection_count"] == 1
    assert metrics["authority"] is False
    assert llm_adapter_metrics(None) == {"present": False}


def test_llm_mock_paraphrase_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "llm_mock_paraphrase", {})
    assert result.success, result.error
    assert result.metrics["paraphrased"] is True
    assert result.metrics["content_preserved"] is True
    assert result.metrics["audited"] is True


def test_llm_grounding_failure_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "llm_grounding_failure", {})
    assert result.success, result.error
    assert result.metrics["fallback_used"] is True
    assert result.metrics["grounding_failures"] >= 1
    assert result.metrics["not_marked_paraphrased"] is True


def test_llm_claim_guard_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "llm_claim_guard", {})
    assert result.success, result.error
    assert result.metrics["safe_passes"] is True
    assert result.metrics["unsafe_handled"] is True
    assert result.metrics["nothing_unsafe_escapes"] is True


def test_llm_classification_assist_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "llm_classification_assist", {})
    assert result.success, result.error
    assert result.metrics["resolved_safely"] is True
    assert result.metrics["unsafe_not_overridden"] is True
    assert result.metrics["overrides_blocked"] is True


def test_llm_report_polish_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "llm_report_polish", {})
    assert result.success, result.error
    assert result.metrics["good_accepted"] is True
    assert result.metrics["bad_rejected"] is True
    assert result.metrics["bad_falls_back_to_raw"] is True
