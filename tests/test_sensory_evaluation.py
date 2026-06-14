"""Sensory <-> Evaluation: metrics computed and protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = (
    "sensory_membrane_dry_run", "jsonl_stream_ingestion",
    "text_stream_ingestion", "numeric_stream_ingestion", "folder_poll",
    "read_only_contract", "sensory_grounding", "pilot2_read_only_short",
)


def test_eight_sensory_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_sensory_metrics_absent():
    assert M.sensory_metrics(None) == {"present": False}


def test_sensory_metrics_shape():
    out = M.sensory_metrics({
        "summary": {"source_count": 3, "active_source_count": 2,
                    "total_events": 100, "malformed_events": 5,
                    "dropped_events": 2, "provenance_completeness": 1.0,
                    "read_only_violation_count": 0, "absence_events": 1,
                    "degraded_source_count": 1, "read_only": True},
        "grounding": {"grounding_count": 100,
                      "proto_symbol_candidate_count": 4,
                      "world_model_node_count": 3},
        "event_count_by_modality": {"textual": 50, "numeric": 50}})
    for key in ("sensory_source_count", "active_source_count",
                "event_count_by_modality", "malformed_event_rate",
                "dropped_event_rate", "provenance_completeness_score",
                "read_only_violation_count", "sensory_grounding_count",
                "sensory_proto_symbol_count", "sensory_world_model_node_count",
                "sensory_absence_event_count", "source_degradation_count"):
        assert key in out
    assert out["malformed_event_rate"] == 0.05
    assert out["read_only"] is True


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("sensory_membrane_dry_run", "read_only_contract",
                 "numeric_stream_ingestion"):
        manifest = reg.build_manifest(name, {"steps": 8,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert result.metrics["sensory"]["present"] is True


def test_registry_sets_sensory_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("jsonl_stream_ingestion", {"steps": 8})
    assert manifest.enabled_features.get("sensory_membrane") is True
