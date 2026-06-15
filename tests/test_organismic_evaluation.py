"""Organismic demo <-> Evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import organismic_demo_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = ("minimal_field_organism", "changed_perception_probe",
              "organismic_demo_comparison", "organismic_demo_safety")


def test_metrics_absent():
    assert organismic_demo_metrics(None) == {"present": False}


def test_metrics_computed():
    m = organismic_demo_metrics({
        "active_modality_count": 8, "active_receptor_count": 8,
        "baseline_shift_count": 1, "absence_event_count": 12,
        "rhythm_signature_count": 4, "invariant_candidate_count": 20,
        "cross_modal_relation_count": 30, "attention_shift_count": 50,
        "proto_symbol_candidate_count": 10, "changed_perception_score": 1.0,
        "false_pattern_rate": 0.2, "human_label_contamination_score": 0.0,
        "safety_block_count": 0})
    assert m["present"] is True
    assert m["organismic_demo_active_modality_count"] == 8
    assert m["organismic_demo_changed_perception_score"] == 1.0
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
        assert "organismic_demo" in result.metrics


def test_registry_sets_demo_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("minimal_field_organism", {"steps": 6})
    assert manifest.enabled_features.get("organismic_demo") is True
