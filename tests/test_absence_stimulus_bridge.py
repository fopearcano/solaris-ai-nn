"""Tests for the absence-stimulus bridge experiment."""

from __future__ import annotations

import time

from solaris_ai_nn.experiments.absence_stimulus_bridge import run_absence_stimulus_bridge


def test_absence_experiment_runs_bounded():
    start = time.perf_counter()
    result = run_absence_stimulus_bridge(presence_steps=30, silence_steps=30, seed=5)
    elapsed = time.perf_counter() - start
    assert elapsed < 30.0  # no infinite loop
    assert result.presence_events == 30
    assert result.silence_events == 30
    assert result.telemetry_report["events"] == 60


def test_reservoir_changes_during_silence():
    result = run_absence_stimulus_bridge(presence_steps=20, silence_steps=40, seed=5)
    # The substrate keeps moving during silence: state drifts and stays active.
    assert result.silence_state_drift > 0.0
    assert result.energy_silence_mean > 0.0
    assert result.went_inert is False


def test_silence_energy_is_not_constant():
    result = run_absence_stimulus_bridge(presence_steps=10, silence_steps=40, seed=5)
    energies = result.energies_silence
    assert len(energies) == 40
    # Escalating absence intensity => the energy trace varies, not frozen.
    assert max(energies) - min(energies) > 1e-6


def test_absence_experiment_is_deterministic():
    a = run_absence_stimulus_bridge(presence_steps=20, silence_steps=20, seed=9)
    b = run_absence_stimulus_bridge(presence_steps=20, silence_steps=20, seed=9)
    assert a.silence_state_drift == b.silence_state_drift
    assert a.energies_silence == b.energies_silence
