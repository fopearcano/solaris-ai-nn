"""Tests for LOGOS evaluation metrics + protocols."""

from __future__ import annotations

from solaris_ai_nn.evaluation import metrics as M
from solaris_ai_nn.evaluation.experiment_registry import ExperimentRegistry
from solaris_ai_nn.evaluation.protocols import PROTOCOLS

LOGOS_PROTOCOLS = ("fracture_detection", "synthesis_candidate",
                   "complexity_regulation", "esc_process",
                   "logos_world_model_contradiction",
                   "logos_proto_symbol_ambiguity", "logos_safety")


def test_metrics_absent():
    assert M.logos_metrics(None) == {"present": False}


def test_metrics_computed(tmp_path):
    from solaris_ai_nn.logos_complexity import LogosComplexityEngine

    engine = LogosComplexityEngine(state_dir=tmp_path)
    engine.tick({"world_model": {"contradiction_edges": ["a|c|b"]},
                 "proto_language": {"symbol_count": 20,
                                    "ambiguous_symbol_count": 10,
                                    "ambiguous_symbols": ["S1"]},
                 "mysterium_pressure": 0.6})
    out = M.logos_metrics(engine.snapshot())
    assert out["present"] is True
    assert out["tension_count"] >= 1
    assert "complexity_band" in out
    assert "complexity_band_distribution" in out
    assert out["authority"] is False


def test_seven_protocols_registered():
    for name in LOGOS_PROTOCOLS:
        assert name in PROTOCOLS


def test_registry_describes_protocols():
    reg = ExperimentRegistry()
    for name in LOGOS_PROTOCOLS:
        assert name in reg.list_experiments()
        manifest = reg.build_manifest(name, {"steps": 40})
        assert manifest.description
        assert manifest.enabled_features.get("logos_complexity") is True


def test_protocols_return_results(tmp_path):
    reg = ExperimentRegistry()
    for name in LOGOS_PROTOCOLS:
        manifest = reg.build_manifest(
            name, {"steps": 40, "state_dir": str(tmp_path / name)})
        result = PROTOCOLS[name](manifest)
        assert result.success, f"{name}: {result.error}"
