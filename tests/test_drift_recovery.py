"""Tests for drift recovery."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.drift_recovery import (
    DriftClass,
    DriftRecoveryManager,
)


def test_healthy_drift_not_repaired_away():
    mgr = DriftRecoveryManager()
    assert mgr.classify({"drift": {"classification": "healthy_slow"}}) == \
        DriftClass.HEALTHY_ADAPTATION
    assert mgr.propose({"drift": {"classification": "healthy_slow"}}) == []


def test_runaway_drift_proposes_stabilization():
    mgr = DriftRecoveryManager()
    actions = mgr.propose({"drift": {"classification": "fast_warning",
                                     "drift_velocity": 3.0}})
    types = {a.action_type for a in actions}
    assert "switch_to_stabilization_mode" in types
    assert "rollback_last_plasticity_update" in types


def test_uncertain_drift_requests_report():
    mgr = DriftRecoveryManager()
    actions = mgr.propose({"drift": {}})
    types = {a.action_type for a in actions}
    assert "generate_operator_review_request" in types
    assert "switch_to_stabilization_mode" in types


def test_instability_classification():
    mgr = DriftRecoveryManager()
    assert mgr.classify({"drift": {"classification": "fast_warning",
                                   "drift_velocity": 0.5}}) == \
        DriftClass.INSTABILITY


def test_stagnation_classification():
    mgr = DriftRecoveryManager()
    assert mgr.classify({"drift": {"classification": "inert_warning"}}) == \
        DriftClass.STAGNATION
    actions = mgr.propose({"drift": {"classification": "inert_warning"}})
    assert any(a.action_type == "request_latent_replay" for a in actions)
