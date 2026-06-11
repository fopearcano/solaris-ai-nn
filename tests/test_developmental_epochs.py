"""Tests for developmental epochs."""

from __future__ import annotations

from solaris_ai_nn.developmental.epochs import (
    DevelopmentalEpoch,
    EpochManager,
)


def test_epoch_manager_starts_bootstrapping():
    manager = EpochManager()
    assert manager.state.current == DevelopmentalEpoch.BOOTSTRAPPING
    assert len(DevelopmentalEpoch.ALL) == 9
    assert manager.snapshot()["note"].startswith("an epoch is a label")


def test_transition_candidate_logged():
    manager = EpochManager()
    transition = manager.evaluate({"total_observed_stimuli": 60},
                                  lifetime_s=100.0)
    assert transition is not None
    assert transition.to_epoch == DevelopmentalEpoch.EARLY_EXPOSURE
    assert transition.reason == "total stimuli >= 50"
    assert transition.signals["total_observed_stimuli"] == 60
    assert manager.state.current == DevelopmentalEpoch.EARLY_EXPOSURE
    assert manager.state.transitions[-1] is transition
    # Transitions depend on metrics: the next rung needs habit signals.
    assert manager.evaluate({"total_observed_stimuli": 999}) is None
    forward = manager.evaluate({"stable_habit_count": 3})
    assert forward.to_epoch == DevelopmentalEpoch.HABIT_FORMATION


def test_uncertain_regression_possible():
    manager = EpochManager()
    manager.evaluate({"total_observed_stimuli": 60})
    regression = manager.evaluate({"prediction_accuracy_trend": -0.5})
    assert regression is not None
    assert regression.to_epoch == DevelopmentalEpoch.UNCERTAIN_REGRESSION
    assert regression.uncertain is True
    assert "regression signal" in regression.reason
    # Recovery restores the previous label, marked uncertain.
    recovery = manager.evaluate({"prediction_accuracy_trend": 0.0})
    assert recovery is not None
    assert recovery.to_epoch == DevelopmentalEpoch.EARLY_EXPOSURE
    assert recovery.uncertain is True


def test_boundary_violations_trigger_regression():
    manager = EpochManager()
    transition = manager.evaluate({"boundary_violation_count": 3})
    assert transition.to_epoch == DevelopmentalEpoch.UNCERTAIN_REGRESSION
