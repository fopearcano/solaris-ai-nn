"""Tests for the linear readout, online learning, habit, and synthesis."""

from __future__ import annotations

from solaris_ai_nn.plasticity.habit_reinforcement import HabitReinforcement
from solaris_ai_nn.plasticity.synthesis_pruning import SynthesisPruner
from solaris_ai_nn.reservoir.online_learning import DeltaRuleLearner
from solaris_ai_nn.reservoir.readout import LinearReadout


def test_readout_starts_zero_and_predicts_zero():
    r = LinearReadout(n_features=4, n_outputs=2)
    assert r.predict([1.0, 2.0, 3.0, 4.0]) == [0.0, 0.0]
    assert r.nonzero_count() == 0


def test_online_update_changes_weights_and_reduces_error():
    r = LinearReadout(n_features=3, n_outputs=2)
    learner = DeltaRuleLearner(lr=0.1)
    features = [1.0, 0.5, -0.2]
    target = 1.0

    first_error = learner.update(r, features, chosen=0, valence=target)
    assert r.nonzero_count() > 0  # weights moved

    # Repeated updates toward the same target shrink the prediction error.
    for _ in range(50):
        last_error = learner.update(r, features, chosen=0, valence=target)
    assert abs(last_error) < abs(first_error)
    # Row 1 was never chosen, so it stays untouched.
    assert all(w == 0.0 for w in r.weights[1])


def test_weight_clip_bounds_weights():
    r = LinearReadout(n_features=2, n_outputs=1)
    learner = DeltaRuleLearner(lr=5.0, weight_clip=2.0)
    for _ in range(100):
        learner.update(r, [1.0, 1.0], chosen=0, valence=1.0)
    assert all(abs(w) <= 2.0 + 1e-9 for w in r.weights[0])


def test_habit_reinforces_repeated_pathway():
    habit = HabitReinforcement(lr=0.2)
    for _ in range(10):
        habit.observe("Stimulus:1", "approach", valence=1.0)
    bias = habit.bias_for("Stimulus:1", "approach")
    assert bias > 0.5  # repeated positive reactions strengthen the pathway
    assert habit.counts[("Stimulus:1", "approach")] == 10
    assert habit.strong_count() == 1


def test_habit_negative_pathway_goes_negative():
    habit = HabitReinforcement(lr=0.3)
    for _ in range(5):
        habit.observe("Stimulus:2", "approach", valence=-1.0)
    assert habit.bias_for("Stimulus:2", "approach") < -0.5


def test_habit_bias_vector_alignment():
    habit = HabitReinforcement(lr=0.5, bias_scale=1.0)
    habit.observe("k", "b", valence=1.0)
    vec = habit.bias_vector("k", ["a", "b", "c"])
    assert vec[0] == 0.0 and vec[2] == 0.0
    assert vec[1] > 0.0


def test_synthesis_prunes_weak_readout_weights():
    r = LinearReadout(n_features=3, n_outputs=1)
    r.weights[0] = [0.001, 0.5, -0.002]  # two weak, one strong
    pruner = SynthesisPruner(readout_threshold=0.01)
    report = pruner.prune(r)
    assert report.readout_zeroed == 2
    assert r.weights[0] == [0.0, 0.5, 0.0]
    assert "subtracted" in report.summary()
    assert len(report.removed) == 2
    assert all(rm.reason for rm in report.removed)


def test_synthesis_prunes_weak_habits():
    habit = HabitReinforcement()
    habit.weights[("k", "a")] = 0.01  # weak
    habit.weights[("k", "b")] = 0.9  # strong
    pruner = SynthesisPruner(habit_threshold=0.05)
    report = pruner.prune(LinearReadout(n_features=2, n_outputs=1), habit)
    assert report.habits_forgotten == 1
    assert ("k", "a") not in habit.weights
    assert ("k", "b") in habit.weights
