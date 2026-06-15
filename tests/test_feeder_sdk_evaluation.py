"""Feeder SDK <-> Evaluation: metrics computed; protocols return results."""

from __future__ import annotations

from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.metrics import feeder_sdk_metrics
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

_PROTOCOLS = ("feeder_sdk_contract", "feeder_sdk_validation",
              "feeder_sdk_privacy", "feeder_sdk_monitor", "feeder_sdk_replay",
              "feeder_sdk_safety")


def test_metrics_absent():
    assert feeder_sdk_metrics(None) == {"present": False}


def test_metrics_computed():
    m = feeder_sdk_metrics({
        "feeder_sdk_envelope_count": 12, "feeder_sdk_valid_event_count": 11,
        "feeder_sdk_invalid_event_count": 1,
        "feeder_sdk_active_output_count": 2,
        "feeder_sdk_silent_output_count": 1,
        "feeder_sdk_privacy_warning_count": 0,
        "feeder_sdk_safety_warning_count": 0,
        "feeder_sdk_schema_coverage": 0.875,
        "feeder_sdk_replay_event_count": 8})
    assert m["present"] is True
    assert m["feeder_sdk_envelope_count"] == 12
    assert m["feeder_sdk_schema_coverage"] == 0.875
    assert m["solaris_controls_feeders"] is False


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
        assert "feeder_sdk" in result.metrics


def test_registry_sets_feeder_sdk_feature():
    reg = ExperimentRegistry()
    manifest = reg.build_manifest("feeder_sdk_contract", {"steps": 6})
    assert manifest.enabled_features.get("feeder_sdk") is True
