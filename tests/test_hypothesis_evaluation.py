"""Tests for hypothesis evaluation metrics + protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

HYP_PROTOCOLS = ("hypothesis_generation", "bounded_self_experiment",
                 "falsification", "delayed_consequence_hypothesis",
                 "proto_symbol_hypothesis", "world_model_edge_hypothesis",
                 "hypothesis_safety")


def test_metrics_absent():
    assert M.hypothesis_metrics(None) == {"present": False}


def test_metrics_computed():
    snap = {
        "memory": {"hypothesis_count": 10,
                   "counts_by_status": {"supported": 2, "falsified": 1,
                                        "inconclusive": 3},
                   "long_lived_unknown_count": 1},
        "test_runner": {"tests_run": 6, "unsafe_count": 1,
                        "evidence": {"evidence_count": 6}},
        "generator": {"generated_total": 10, "distinct_keys": 8},
        "mysterium_reduction_after_tests": 0.1,
    }
    out = M.hypothesis_metrics(snap)
    assert out["present"] is True
    assert out["hypothesis_count"] == 10
    assert out["test_count"] == 6
    assert out["support_rate"] == round(2 / 6, 4)
    assert out["falsification_rate"] == round(1 / 6, 4)
    assert out["hypothesis_reuse_rate"] == round(1 - 8 / 10, 4)
    assert out["authority"] is False


def test_seven_protocols_registered():
    for name in HYP_PROTOCOLS:
        assert name in PROTOCOLS


def test_registry_describes_protocols():
    reg = ExperimentRegistry()
    for name in HYP_PROTOCOLS:
        assert name in reg.list_experiments()
        manifest = reg.build_manifest(name, {"steps": 60})
        assert manifest.description
        assert manifest.enabled_features.get("hypothesis_engine") is True


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in HYP_PROTOCOLS:
        manifest = reg.build_manifest(
            name, {"steps": 60, "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
