"""Sensorium lab <-> Evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import sensorium_lab_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = ("sensorium_lab_study", "sensorium_lab_comparison",
              "sensorium_lab_safety", "sensorium_world_signature",
              "sensorium_ontology_drift")


def test_metrics_absent():
    assert sensorium_lab_metrics(None) == {"present": False}


def test_metrics_computed():
    m = sensorium_lab_metrics({
        "sensorium_arm_count": 9, "world_signature_count": 8,
        "modality_fingerprint_count": 20, "structural_difference_score": 0.4,
        "strongest_difference_strength": "strong", "ontology_drift_score": 0.7,
        "modality_native_structure_ratio": 0.9,
        "human_label_contamination_score": 0.1,
        "inconclusive_sensorium_comparison_count": 1,
        "sensorium_negative_result_count": 2})
    assert m["present"] is True
    assert m["sensorium_arm_count"] == 9
    assert m["strongest_difference_strength"] == "strong"
    assert m["ranks_sensoriums"] is False


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
        assert "sensorium_lab" in result.metrics


def test_registry_sets_sensorium_lab_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("sensorium_lab_study", {"steps": 6})
    assert manifest.enabled_features.get("sensorium_lab") is True
