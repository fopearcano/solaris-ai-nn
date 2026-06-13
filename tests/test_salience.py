"""Tests for the salience estimator."""

from __future__ import annotations

from solaris_ai_nn.active_perception.salience import (
    SalienceCategory,
    SalienceEstimator,
)


def test_high_mysterium_creates_salience():
    est = SalienceEstimator()
    smap = est.estimate({"mysterium_pressure": 0.8})
    assert smap.signals
    top = smap.top()
    assert top.source == "mysterium"


def test_safety_salience_dominates_curiosity():
    est = SalienceEstimator()
    smap = est.estimate({"mysterium_pressure": 0.9, "emergency": True,
                         "novelty_rate": 0.9})
    top = smap.top()
    assert top.category == SalienceCategory.SAFETY
    assert smap.has_safety_salience() is True


def test_rank_targets_deterministic():
    est = SalienceEstimator()
    ctx = {"mysterium_pressure": 0.6, "novelty_rate": 0.2,
           "world_model": {"graph_node_count": 5, "unknown_node_count": 2,
                           "low_confidence_nodes": ["n1"]}}
    a = [s.target_ref for s in est.estimate(ctx).rank_targets(10)]
    b = [s.target_ref for s in est.estimate(ctx).rank_targets(10)]
    assert a == b


def test_empty_context_has_no_curiosity_salience():
    est = SalienceEstimator()
    smap = est.estimate({})
    assert smap.top() is None


def test_low_confidence_node_is_salient():
    est = SalienceEstimator()
    smap = est.estimate({"world_model": {"graph_node_count": 10,
                                         "unknown_node_count": 4,
                                         "low_confidence_nodes": ["nx"]}})
    targets = [s.target_ref for s in smap.rank_targets(10)]
    assert "nx" in targets


def test_snapshot_shape():
    est = SalienceEstimator()
    est.estimate({"mysterium_pressure": 0.5})
    snap = est.snapshot()
    assert "ranked" in snap
