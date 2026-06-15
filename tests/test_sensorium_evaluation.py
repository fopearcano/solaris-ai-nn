"""Plural sensorium <-> Evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import plural_sensorium_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = ("plural_sensorium_fixture", "human_like_sensorium",
              "non_human_sensorium", "mixed_sensorium", "continuous_field",
              "receptor_adaptation", "cross_modal_sensorium",
              "sensorium_grounding", "plural_sensorium_safety")


def test_metrics_absent():
    assert plural_sensorium_metrics(None) == {"present": False}


def test_metrics_computed():
    m = plural_sensorium_metrics({
        "active_modality_count": 3, "active_receptor_count": 4,
        "sensory_field_pressure": 0.5, "absence_pressure": 0.2,
        "novelty_pressure": 0.3, "rhythm_pressure": 0.4,
        "cross_modal_pressure": 0.1, "receptor_adaptation_count": 2,
        "baseline_shift_count": 1, "flux_event_count": 5,
        "absence_event_count": 1, "rhythm_signature_count": 2,
        "invariant_candidate_count": 3, "cross_modal_relation_count": 2,
        "modality_grounded_proto_symbol_count": 1,
        "modality_native_grounding_score": 0.8,
        "human_label_contamination_score": 0.0})
    assert m["present"] is True
    assert m["active_modality_count"] == 3
    assert m["modality_grounded_proto_symbol_count"] == 1
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
        assert "sensorium" in result.metrics


def test_registry_sets_sensorium_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("plural_sensorium_fixture", {"steps": 6})
    assert manifest.enabled_features.get("plural_sensorium") is True
