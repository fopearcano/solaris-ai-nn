"""Tests for ecology evaluation metrics, protocols, and registry."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

ECOLOGY_PROTOCOLS = ("nursery_short_run", "absence_deprivation",
                     "delayed_consequence", "seasonal_shift",
                     "anomaly_adaptation", "ecology_proto_symbol")


def test_ecology_metrics_absent():
    assert M.ecology_metrics(None) == {"present": False}


def test_ecology_metrics_shape():
    ecology = {"ecology_event_count": 50, "absence_window_count": 8,
               "novelty_rate": 0.1, "anomaly_rate": 0.05,
               "delayed_consequence_group_count": 4,
               "seasonal_shift_count": 2, "event_rate": 0.5}
    memory = {"event_counts": {"regular_signal": 30, "anomaly": 5,
                               "novel_signal": 5, "absence_window": 10},
              "deprivation_windows": 8}
    response = {"delayed_consequence_associations": 2,
                "ecology_symbol_emergence_count": 3}
    out = M.ecology_metrics(ecology, memory, response)
    assert out["present"] is True
    assert out["ecology_event_count"] == 50
    assert 0.0 <= out["event_distribution_entropy"] <= 1.0
    assert out["delayed_consequence_resolution_rate"] == 0.5
    assert out["ecology_symbol_emergence_count"] == 3
    assert out["authority"] is False


def test_six_ecology_protocols_registered():
    for name in ECOLOGY_PROTOCOLS:
        assert name in PROTOCOLS


def test_registry_describes_ecology_protocols():
    reg = ExperimentRegistry()
    for name in ECOLOGY_PROTOCOLS:
        assert name in reg.list_experiments()
        manifest = reg.build_manifest(name, {"steps": 60})
        assert manifest.description


def test_ecology_protocols_run(tmp_path):
    reg = ExperimentRegistry()
    for name in ECOLOGY_PROTOCOLS:
        manifest = reg.build_manifest(
            name, {"steps": 80, "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
        assert result.metrics.get("ecology", {}).get("present") is True


def test_nursery_short_run_deterministic(tmp_path):
    reg = ExperimentRegistry()
    manifest = reg.build_manifest(
        "nursery_short_run", {"steps": 80,
                              "state_dir": str(tmp_path / "nsr")})
    result = PROTOCOLS["nursery_short_run"](manifest)
    assert result.metrics["deterministic_with_seed"] is True
