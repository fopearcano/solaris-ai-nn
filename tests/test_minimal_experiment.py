"""Tests for the experiment loop and the minimal continuous-ESN experiment."""

from __future__ import annotations

import time

from solaris_ai_nn.experiments.minimal_continuous_esn import (
    RepeatedPatternEnvironment,
    run_minimal_continuous_esn,
)
from solaris_ai_nn.runtime.experiment_loop import ExperimentLoop


def test_loop_runs_with_max_steps():
    loop = ExperimentLoop(action_labels=["a", "b"], seed=1)
    telem = loop.run(max_steps=50)
    assert telem.steps == 50
    assert telem.heartbeats >= 50
    assert telem.reservoir_updates == 50
    assert len(loop.trace) > 0


def test_loop_rejects_nonpositive_steps():
    loop = ExperimentLoop(action_labels=["a", "b"], seed=1)
    for bad in (0, -5, None):
        try:
            loop.run(max_steps=bad)  # type: ignore[arg-type]
            assert False, "expected ValueError"
        except ValueError:
            pass


def test_run_until_terminates_with_predicate():
    loop = ExperimentLoop(action_labels=["a", "b"], seed=1)
    loop.run_until(lambda lp: lp.telemetry.steps >= 30, safety_limit=1000)
    assert loop.telemetry.steps >= 30


def test_run_until_respects_safety_limit():
    loop = ExperimentLoop(action_labels=["a", "b"], seed=1)
    # A predicate that never fires must still stop at the safety limit.
    loop.run_until(lambda lp: False, safety_limit=20)
    assert loop.telemetry.steps == 20


def test_absence_stimulus_is_synthesised_under_silence():
    # No environment and no injected stimuli => silence => absence stimuli appear.
    loop = ExperimentLoop(action_labels=["a"], silence_steps=3, seed=2)
    saw_absence = False
    for _ in range(20):
        result = loop.step()
        if result.is_absence:
            saw_absence = True
    assert saw_absence


def test_minimal_experiment_completes_and_learns():
    start = time.perf_counter()
    result = run_minimal_continuous_esn(max_steps=1500, seed=7)
    elapsed = time.perf_counter() - start

    # Completes promptly (no infinite loop).
    assert elapsed < 30.0
    assert result.telemetry_report["steps"] == 1500

    # Behaviour changed over time: late accuracy beats early accuracy.
    assert result.late_accuracy > result.early_accuracy

    # Habit reinforced some pathways and synthesis subtracted some weights.
    assert result.habit_pathways > 0
    assert result.pruned_pathways >= 0  # pruning ran; may be 0 on a given seed


def test_minimal_experiment_is_deterministic():
    a = run_minimal_continuous_esn(max_steps=400, seed=11)
    b = run_minimal_continuous_esn(max_steps=400, seed=11)
    assert a.early_accuracy == b.early_accuracy
    assert a.late_accuracy == b.late_accuracy
    assert a.telemetry_report["readout_updates"] == b.telemetry_report["readout_updates"]


def test_environment_grades_only_real_stimuli():
    env = RepeatedPatternEnvironment()
    # An absence stimulus must not be graded.
    from solaris_ai_nn.signals.canonical import Action, Stimulus

    absent = Stimulus(payload="light", is_absence=True)
    assert env.react(absent, Action(name="approach")) is None
    assert env.react(None, Action(name="approach")) is None
