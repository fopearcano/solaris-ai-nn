"""Live field <-> Evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import live_field_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = ("live_field_preflight", "live_field_pilot",
              "live_field_comparison", "live_field_safety")


def test_metrics_absent():
    assert live_field_metrics(None) == {"present": False}


def test_metrics_computed():
    m = live_field_metrics({
        "feeder_count": 3, "active_source_count": 2, "silent_source_count": 1,
        "corrupt_source_count": 0, "active_modality_count": 2,
        "source_unpredictability_score": 0.3, "baseline_shift_count": 1,
        "absence_event_count": 2, "rhythm_signature_count": 1,
        "invariant_candidate_count": 4, "cross_modal_relation_count": 3,
        "changed_perception_score": 0.8, "human_label_contamination_score": 0.0,
        "safety_block_count": 0})
    assert m["present"] is True
    assert m["live_feeder_count"] == 3
    assert m["live_changed_perception_score"] == 0.8
    assert m["controls_hardware"] is False


def test_protocols_registered():
    for name in _PROTOCOLS:
        assert name in PROTOCOLS


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in _PROTOCOLS:
        manifest = reg.build_manifest(name, {"steps": 6,
                                             "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, result.error
        assert "live_field" in result.metrics


def test_registry_sets_live_field_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("live_field_pilot", {"steps": 6})
    assert manifest.enabled_features.get("live_field") is True
