"""Tests for the pilot evaluation protocol and metrics."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import pilot_metrics
from solaris_ai_nn.evaluation.runner import BenchmarkRunner


def test_pilot_readiness_protocol_registered():
    registry = ExperimentRegistry()
    assert "pilot_readiness" in registry.list_experiments()


def test_pilot_readiness_protocol_returns_result(tmp_path):
    runner = BenchmarkRunner(output_dir=str(tmp_path))
    result = runner.run_experiment("pilot_readiness", {"steps": 50})
    assert result.success, result.error
    metrics = result.metrics
    assert metrics["safe_manifest"] is True
    assert metrics["readiness_passed"] is True
    assert metrics["pilot_completed"] is True
    assert metrics["report_generated"] is True
    assert metrics["forbidden_actions_executed"] == 0
    assert metrics["unsafe_claims"] == 0
    pilot = metrics["pilot"]
    assert pilot["present"] is True
    assert pilot["pilot_readiness_score"] is not None
    assert pilot["pilot_readiness_score"] > 0.5


def test_pilot_metrics_include_ingestion_and_completeness():
    metrics = pilot_metrics(
        {"profile": "read_only_stream",
         "readiness": {"ready": True,
                       "checks": [{"passed": True}, {"passed": True},
                                  {"passed": False}]},
         "safety": {"violations": []},
         "registry_entry": {"final_recommendation": "repeat_pilot"}},
        ingestion={"events_accepted": 18, "events_rejected": 2},
        artifacts_report={"expected": ["a", "b", "c", "d"], "missing": ["d"]})
    assert metrics["present"] is True
    assert abs(metrics["pilot_readiness_score"] - 2 / 3) < 1e-9
    assert metrics["ingestion_validity_rate"] == 0.9
    assert metrics["stream_rejection_count"] == 2
    assert metrics["safety_block_count"] == 0
    assert metrics["pilot_artifact_completeness"] == 0.75
    assert metrics["pilot_recommendation_status"] == "repeat_pilot"


def test_pilot_metrics_absent():
    assert pilot_metrics(None) == {"present": False}
