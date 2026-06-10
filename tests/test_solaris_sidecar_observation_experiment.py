"""Tests for the sidecar observation experiment (fake runtime)."""

from __future__ import annotations

import time
from pathlib import Path

from solaris_ai_nn.experiments.solaris_sidecar_observation import (
    run_sidecar_observation,
)


def test_bounded_experiment_runs():
    start = time.perf_counter()
    result = run_sidecar_observation(steps=50, seed=7)
    elapsed = time.perf_counter() - start
    assert elapsed < 30.0  # no infinite loop
    assert result.signals_emitted >= 50
    assert result.signals_observed == result.signals_emitted


def test_suggestions_are_produced():
    result = run_sidecar_observation(steps=50, seed=7)
    assert result.suggestions_produced > 0
    assert result.reactions_learned > 0
    assert result.mirrored == result.signals_observed


def test_no_committed_actions_ever():
    for observe_only in (True, False):
        result = run_sidecar_observation(steps=40, seed=3, observe_only=observe_only)
        assert result.committed_actions == 0
        assert result.conscience_death_calls == 0


def test_observe_only_publishes_nothing_but_publish_mode_does():
    held = run_sidecar_observation(steps=40, seed=3, observe_only=True)
    assert held.suggestions_published == 0
    publishing = run_sidecar_observation(steps=40, seed=3, observe_only=False)
    assert publishing.suggestions_published > 0


def test_persists_state(tmp_path):
    state_dir = tmp_path / "sidecar"
    run_sidecar_observation(steps=30, seed=3, state_dir=str(state_dir))
    assert (state_dir / "integration_state.json").exists()
    assert (state_dir / "suggestions.jsonl").exists()
    assert (state_dir / "mirrored_signals.jsonl").exists()


def test_deterministic_per_seed():
    a = run_sidecar_observation(steps=40, seed=9)
    b = run_sidecar_observation(steps=40, seed=9)
    assert a.suggestions_produced == b.suggestions_produced
    assert a.reactions_learned == b.reactions_learned
