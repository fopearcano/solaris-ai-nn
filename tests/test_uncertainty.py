"""Tests for the uncertainty estimator."""

from __future__ import annotations

from solaris_ai_nn.active_perception.uncertainty import (
    UncertaintyEstimator,
    UncertaintySource,
)


def test_low_confidence_world_node_creates_uncertainty():
    est = UncertaintyEstimator()
    state = est.estimate({"world_model": {"graph_node_count": 10,
                                          "unknown_node_count": 5,
                                          "prediction_accuracy": 0.3,
                                          "low_confidence_nodes": ["nx"]}})
    sources = {t.source for t in state.targets}
    assert UncertaintySource.WORLD_MODEL_CONFIDENCE in sources
    assert state.sufficient_evidence is True


def test_ambiguous_symbol_creates_uncertainty():
    est = UncertaintyEstimator()
    state = est.estimate({"proto_language": {"symbol_count": 8,
                                             "ambiguous_symbol_count": 4,
                                             "ambiguous_symbols": ["S1"]}})
    sources = {t.source for t in state.targets}
    assert UncertaintySource.PROTO_SYMBOL_AMBIGUITY in sources


def test_insufficient_evidence_reports_unknown():
    est = UncertaintyEstimator()
    state = est.estimate({})
    assert state.sufficient_evidence is False
    assert state.targets == []
    assert state.top() is None


def test_top_uncertain_targets_sorted():
    est = UncertaintyEstimator()
    est.estimate({"mysterium_pressure": 0.9,
                  "world_model": {"graph_node_count": 4,
                                  "unknown_node_count": 1,
                                  "prediction_accuracy": 0.9}})
    targets = est.top_uncertain_targets(10)
    uncertainties = [t.uncertainty for t in targets]
    assert uncertainties == sorted(uncertainties, reverse=True)


def test_snapshot_shape():
    est = UncertaintyEstimator()
    est.estimate({"mysterium_pressure": 0.4})
    snap = est.snapshot()
    assert "overall" in snap and "top_targets" in snap
