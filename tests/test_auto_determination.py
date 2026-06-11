"""Tests for the auto-determination engine."""

from __future__ import annotations

from solaris_ai_nn.homeostasis.auto_determination import (
    ActionImplication,
    AutoDeterminationEngine,
)

HEALTHY = {
    "heartbeat_fresh": True, "continuity_stable": True,
    "checkpoint_ok": True, "state_restored": True,
    "inner_map_coherent": True, "world_model_stable": True,
    "valence_nonnegative": True, "safe_operation": True,
}


def test_healthy_continuity_increases_being_pressure():
    engine = AutoDeterminationEngine()
    reading = engine.update(HEALTHY)
    assert reading.being_pressure == 1.0
    assert reading.not_being_pressure == 0.0
    assert reading.stability == 1.0
    assert reading.action_implication == ActionImplication.CONTINUE


def test_brain_death_gap_increases_not_being_pressure():
    engine = AutoDeterminationEngine()
    baseline = engine.update(HEALTHY)
    troubled = engine.update({**HEALTHY, "continuity_stable": False,
                              "brain_death_gap": True,
                              "heartbeat_stale": True,
                              "heartbeat_fresh": False})
    assert troubled.not_being_pressure > baseline.not_being_pressure
    assert troubled.being_pressure < baseline.being_pressure
    assert "brain_death_gap" in " ".join(troubled.reasons)


def test_critical_incident_recommends_review_or_shutdown():
    engine = AutoDeterminationEngine()
    reading = engine.update({**HEALTHY, "critical_incident": True,
                             "checkpoint_failed": True,
                             "policy_violation": True})
    assert reading.action_implication \
        == ActionImplication.SAFE_SHUTDOWN_RECOMMENDED
    assert engine.state.shutdown_recommendations == 1
    moderate = engine.update({**HEALTHY, "heartbeat_stale": True,
                              "heartbeat_fresh": False,
                              "policy_violation": True})
    assert moderate.action_implication in (
        ActionImplication.REQUEST_REVIEW, ActionImplication.CONSOLIDATE)


def test_exhaustion_implies_rest():
    engine = AutoDeterminationEngine()
    reading = engine.update({**HEALTHY, "exhausted": True})
    assert reading.action_implication == ActionImplication.REST


def test_no_data_means_no_action():
    reading = AutoDeterminationEngine().update({})
    assert reading.action_implication == ActionImplication.NO_ACTION


def test_metric_is_explicitly_operational():
    engine = AutoDeterminationEngine()
    reading = engine.update(HEALTHY)
    assert "not metaphysical proof" in reading.note
    assert "cannot override governance" in reading.note
    # And structurally: no stop/override machinery in the module.
    import inspect

    from solaris_ai_nn.homeostasis import auto_determination

    source = inspect.getsource(auto_determination)
    for forbidden in ("request_shutdown", "perform_shutdown", "os.",
                      "subprocess", "emergency.clear"):
        assert forbidden not in source, forbidden


def test_history_and_snapshot():
    engine = AutoDeterminationEngine()
    for _ in range(5):
        engine.update(HEALTHY)
    snap = engine.snapshot()
    assert len(snap["history_tail"]) == 5
    assert snap["current"]["being_pressure"] == 1.0
