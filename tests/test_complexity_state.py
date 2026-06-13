"""Tests for complexity state and regulation."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity.complexity_state import (
    ComplexityBand,
    ComplexityRegulator,
)


def test_inert_band_detected():
    reg = ComplexityRegulator()
    state = reg.estimate({"proto_language": {"symbol_count": 0},
                          "stagnation_status": "inert",
                          "mysterium_pressure": 0.0})
    assert state.band == ComplexityBand.INERT


def test_productive_band_detected():
    reg = ComplexityRegulator()
    state = reg.estimate({
        "proto_language": {"symbol_count": 40, "ambiguous_symbol_count": 8},
        "world_model": {"graph_node_count": 20, "graph_edge_count": 30},
        "mysterium_pressure": 0.3})
    assert state.band in (ComplexityBand.PRODUCTIVE,
                          ComplexityBand.COMPLEX_UNSTABLE)


def test_overload_band_detected():
    reg = ComplexityRegulator()
    state = reg.estimate({
        "proto_language": {"symbol_count": 900, "ambiguous_symbol_count":
                           500},
        "mysterium_pressure": 0.95, "memory": {"over_budget": ["hot"]},
        "autoregeneration": {"latest_degradation_severity": "critical"}})
    assert state.band == ComplexityBand.OVERLOADED


def test_unknown_band_without_evidence():
    reg = ComplexityRegulator()
    state = reg.estimate({})
    assert state.band == ComplexityBand.UNKNOWN


def test_no_consciousness_or_life_score():
    reg = ComplexityRegulator()
    state = reg.estimate({"mysterium_pressure": 0.3})
    data = state.to_dict()
    assert "consciousness_score" not in data
    assert "life_score" not in data


def test_recommendation_follows_band():
    reg = ComplexityRegulator()
    inert = reg.estimate({"proto_language": {"symbol_count": 0},
                          "stagnation_status": "inert",
                          "mysterium_pressure": 0.0})
    assert inert.recommendation == "increase_exploration"
    overloaded = reg.estimate({"mysterium_pressure": 0.95,
                               "emergency": True})
    assert overloaded.recommendation == "request_safe_shutdown"
