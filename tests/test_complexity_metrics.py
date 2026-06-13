"""Tests for LOGOS complexity metrics."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity import LogosComplexityEngine
from solaris_ai_nn.logos_complexity.complexity_metrics import (
    compute_complexity_metrics,
)


def _engine(tmp_path):
    engine = LogosComplexityEngine(state_dir=tmp_path)
    engine.tick({"world_model": {"contradiction_edges": ["a|c|b"],
                                 "prediction_accuracy": 0.2},
                 "proto_language": {"symbol_count": 30,
                                    "ambiguous_symbol_count": 15,
                                    "ambiguous_symbols": ["S1"]},
                 "mysterium_pressure": 0.6,
                 "structural_change_score": 0.1})
    engine.tick({"structural_change_score": 0.3})
    return engine


def test_metrics_absent():
    assert compute_complexity_metrics(None) == {"present": False}


def test_metrics_computed(tmp_path):
    metrics = compute_complexity_metrics(_engine(tmp_path).snapshot())
    assert metrics["present"] is True
    assert metrics["tension_count"] >= 1
    assert "complexity_band" in metrics
    assert "synthesis_success_rate" in metrics
    assert metrics["authority"] is False


def test_tension_to_growth_delta(tmp_path):
    metrics = compute_complexity_metrics(_engine(tmp_path).snapshot())
    # Two ticks with structural_change_score 0.1 -> 0.3 give a delta of 0.2.
    assert metrics["tension_to_growth_delta"] == 0.2


def test_no_consciousness_score(tmp_path):
    metrics = compute_complexity_metrics(_engine(tmp_path).snapshot())
    assert "consciousness_score" not in metrics
    assert "life_score" not in metrics
