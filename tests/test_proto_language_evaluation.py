"""Tests for proto-language evaluation metrics and protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import proto_language_metrics
from solaris_ai_nn.evaluation.runner import BenchmarkRunner


def test_proto_language_protocols_registered():
    experiments = ExperimentRegistry().list_experiments()
    for name in ("proto_symbol_emergence", "symbol_compression",
                 "symbol_prediction", "proto_syntax",
                 "symbol_grounding", "proto_language_safety"):
        assert name in experiments, name


def test_proto_language_metrics_computed():
    metrics = proto_language_metrics({
        "symbol_count": 10, "stable_symbol_count": 4,
        "ambiguous_symbol_count": 2, "sequence_count": 6,
        "proto_syntax_rule_count": 2, "compression_utility": 0.3,
        "prediction_utility": 0.15, "first_stable_symbol": "ABS_0001",
        "symbol_explosion_warning_count": 0})
    assert metrics["present"] is True
    assert metrics["proto_symbol_count"] == 10
    assert metrics["ambiguous_symbol_ratio"] == 0.2
    assert metrics["compression_ratio_from_symbols"] == 0.3
    assert metrics["prediction_improvement_over_baseline"] == 0.15
    assert metrics["authority"] is False
    assert "consciousness_score" not in metrics
    assert proto_language_metrics(None) == {"present": False}


def test_emergence_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "proto_symbol_emergence", {})
    assert result.success, result.error
    assert result.metrics["accepted"] >= 3
    assert result.metrics["below_threshold_ignored"] is True
    assert result.metrics["tokens_generated_form"] is True
    assert result.metrics["evidence_required"] is True


def test_compression_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "symbol_compression", {})
    assert result.success, result.error
    assert result.metrics["compressed"] is True
    assert result.metrics["safety_kept_verbatim"] is True
    assert result.metrics["safety_hidden"] == 0


def test_prediction_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "symbol_prediction", {})
    assert result.success, result.error
    assert result.metrics["symbolic_accuracy"] == 1.0
    assert result.metrics["honest_reporting"] is True


def test_syntax_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "proto_syntax", {})
    assert result.success, result.error
    assert result.metrics["rules_inferred"] is True
    assert result.metrics["rule_validated"] is True
    assert result.metrics["vocabulary_cautious"] is True


def test_grounding_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "symbol_grounding", {})
    assert result.success, result.error
    assert result.metrics["stable_when_consistent"] is True
    assert result.metrics["ambiguity_rises_with_spread"] is True
    assert result.metrics["operational_not_understanding"] is True


def test_safety_protocol(tmp_path):
    result = BenchmarkRunner(output_dir=str(tmp_path)).run_experiment(
        "proto_language_safety", {})
    assert result.success, result.error
    assert result.metrics["command_blocked"] is True
    assert result.metrics["counterfactual_rejected"] is True
    assert result.metrics["translation_safe"] is True
    assert result.metrics["no_authority"] is True
