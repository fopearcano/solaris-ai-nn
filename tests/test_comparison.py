"""Tests for cross-run comparisons."""

from __future__ import annotations

from solaris_ai_nn.evaluation.benchmark import ExperimentManifest, ExperimentResult
from solaris_ai_nn.evaluation.comparison import (
    compare_plasticity_modes,
    compare_substrates,
)


def _result(substrate="esn", plasticity=False, adaptation=0.5):
    manifest = ExperimentManifest(name="t", substrate=substrate)
    manifest.enabled_features["plasticity"] = plasticity
    return ExperimentResult(
        manifest=manifest, success=True, started_at=0.0, ended_at=1.0,
        metrics={"scores": {"domains": {
            "adaptation_score": {"score": adaptation, "explanation": "x"},
            "reactivity_score": {"score": 0.8, "explanation": "x"},
            "continuity_score": {"score": 1.0, "explanation": "x"},
        }}})


def test_substrate_comparison_returns_table():
    results = [_result("esn", adaptation=0.4),
               _result("spiking_recurrent", adaptation=0.8)]
    out = compare_substrates(results)
    assert "esn" in out["groups"] and "spiking_recurrent" in out["groups"]
    md = out["markdown"]
    assert md.startswith("| substrate |")
    assert "| esn | 1 |" in md
    assert "0.800" in md


def test_plasticity_comparison_returns_table():
    results = [_result(plasticity=True), _result(plasticity=False)]
    out = compare_plasticity_modes(results)
    assert set(out["groups"]) == {"plasticity_on", "plasticity_off"}
    assert "plasticity_on" in out["markdown"]
