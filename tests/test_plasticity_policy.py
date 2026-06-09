"""Tests for the PlasticityPolicy proposal rules."""

from __future__ import annotations

from solaris_ai_nn.plasticity.policy import PlasticityPolicy


def _targets(steps):
    return {s.target.label() for s in steps}


def test_high_error_proposes_learning_rate_increase():
    policy = PlasticityPolicy()
    ctx = {
        "error_high_streak": 3,
        "recent_error": 0.9,
        "current": {"readout.learning_rate": 0.3},
    }
    steps = policy.propose(ctx)
    lr_steps = [s for s in steps if s.target.label() == "readout.learning_rate"]
    assert lr_steps
    assert lr_steps[0].change.new_value > 0.3


def test_stable_low_error_proposes_stabilization():
    policy = PlasticityPolicy()
    ctx = {
        "error_low_streak": 3,
        "recent_error": 0.1,
        "current": {"readout.learning_rate": 0.3, "bridge.stabilization_tendency": 0.0},
    }
    steps = policy.propose(ctx)
    assert "bridge.stabilization_tendency" in _targets(steps)
    stab = [s for s in steps if s.target.parameter == "stabilization_tendency"][0]
    assert stab.change.new_value > 0.0


def test_unused_pathway_proposes_pruning():
    policy = PlasticityPolicy()
    ctx = {"unused_pathways": 5, "current": {"synthesis.pruning_threshold": 0.01}}
    steps = policy.propose(ctx)
    prune = [s for s in steps if s.target.label() == "synthesis.pruning_threshold"]
    assert prune
    assert prune[0].change.new_value > 0.01


def test_high_fracture_proposes_exploration_increase():
    policy = PlasticityPolicy()
    ctx = {"logos_fracture": 0.8, "current": {"bridge.exploration_tendency": 0.1}}
    steps = policy.propose(ctx)
    expl = [s for s in steps if s.target.label() == "bridge.exploration_tendency"]
    assert expl
    assert expl[0].change.new_value > 0.1


def test_repeatedly_reinforced_habit_proposes_weight_increase():
    policy = PlasticityPolicy()
    ctx = {
        "strongest_habit": {"pattern": "Stimulus:1", "action": "approach",
                             "weight": 0.5, "count": 8},
        "current": {"habit.max_habit_weight": 1.0},
    }
    steps = policy.propose(ctx)
    habit = [s for s in steps if s.target.component == "habit"]
    assert habit
    assert abs(habit[0].change.new_value) > 0.5


def test_calm_context_proposes_nothing():
    policy = PlasticityPolicy()
    steps = policy.propose({"current": {"readout.learning_rate": 0.3}})
    assert steps == []
