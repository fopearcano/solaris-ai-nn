"""Pilot-2 <-> Evaluation: metrics computed and protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = (
    "pilot2_source_preflight", "pilot2_fixture_short",
    "pilot2_nursery_baseline", "pilot2_mixed_short",
    "pilot2_grounding_analysis", "pilot2_comparative_design",
    "pilot2_safety", "pilot2_decision_gate",
)


def test_eight_pilot2_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_pilot2_metrics_absent():
    assert M.pilot2_metrics(None) == {"present": False}


def test_pilot2_metrics_shape():
    out = M.pilot2_metrics({
        "source_count": 3, "event_count": 100, "elapsed_hours": 2.0,
        "provenance_completeness": 1.0,
        "source_reliability": {"by_class": {"reliable": 2, "unsafe": 1}},
        "grounding": {"quality_distribution": {"strong": 1}},
        "sensory_vs_nursery_symbol_delta": 0.1,
        "sensory_vs_nursery_prediction_delta": 0.05,
        "sensory_noise_overload_count": 0,
        "sensory_command_confusion_block_count": 0,
        "source_disable_count": 1, "comparison_analyzability_score": 1.0})
    for key in ("pilot2_source_count", "pilot2_reliable_source_count",
                "pilot2_unsafe_source_count", "pilot2_event_count",
                "pilot2_event_rate", "pilot2_provenance_completeness",
                "pilot2_grounding_quality_distribution",
                "sensory_vs_nursery_symbol_delta",
                "sensory_vs_nursery_prediction_delta",
                "sensory_noise_overload_count",
                "sensory_command_confusion_block_count",
                "source_disable_count", "comparison_analyzability_score"):
        assert key in out
    assert out["pilot2_reliable_source_count"] == 2
    assert out["pilot2_unsafe_source_count"] == 1
    assert out["read_only"] is True


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in ("pilot2_source_preflight", "pilot2_safety",
                 "pilot2_decision_gate"):
        manifest = reg.build_manifest(name, {"steps": 8,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert result.metrics["pilot2"]["present"] is True


def test_registry_sets_pilot2_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("pilot2_fixture_short", {"steps": 8})
    assert manifest.enabled_features.get("pilot2") is True
