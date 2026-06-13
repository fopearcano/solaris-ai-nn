"""Tests for active perception evaluation metrics + protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

AP_PROTOCOLS = ("active_perception_basic", "uncertainty_sampling",
                "curiosity_safety", "stagnation_recovery",
                "proto_symbol_disambiguation",
                "world_model_information_gain", "nursery_active_sampling")


def test_metrics_absent():
    assert M.active_perception_metrics(None) == {"present": False}


def test_metrics_computed():
    snap = {
        "exploration_memory": {"record_count": 4, "useful_rate": 0.5,
                               "blocked_count": 1},
        "attention": {"shifts_total": 3},
        "policy": {"mode": "balanced"},
        "information_gain": {"mean_observed_gain": 0.2},
    }
    rows = [{"mysterium_before": 0.6, "mysterium_after": 0.4,
             "prediction_accuracy_before": 0.4,
             "prediction_accuracy_after": 0.6,
             "proto_symbol_ambiguity_before": 4,
             "proto_symbol_ambiguity_after": 2,
             "expected_information_gain": 0.3,
             "observed_information_gain": 0.25}]
    out = M.active_perception_metrics(snap, rows)
    assert out["present"] is True
    assert out["sampling_action_count"] == 4
    assert out["useful_sampling_rate"] == 0.5
    assert out["blocked_sampling_rate"] == 0.25
    assert out["Mysterium_reduction_after_sampling"] == 0.2
    assert out["proto_symbol_disambiguation_rate"] == 1.0
    assert out["authority"] is False


def test_seven_protocols_registered():
    for name in AP_PROTOCOLS:
        assert name in PROTOCOLS


def test_registry_describes_protocols():
    reg = ExperimentRegistry()
    for name in AP_PROTOCOLS:
        assert name in reg.list_experiments()
        manifest = reg.build_manifest(name, {"steps": 40})
        assert manifest.description
        assert manifest.enabled_features.get("active_perception") is True


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in AP_PROTOCOLS:
        manifest = reg.build_manifest(
            name, {"steps": 40, "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
        assert result.metrics.get("active_perception", {}).get(
            "present") is True
