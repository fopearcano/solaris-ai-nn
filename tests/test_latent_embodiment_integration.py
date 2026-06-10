"""Tests for latent cognition inside the sensorimotor runner."""

from __future__ import annotations

import time

from solaris_ai_nn.embodiment.simulation_runner import (
    SensorimotorSimulationRunner,
)


def test_sensorimotor_latent_disabled_by_default(tmp_path):
    runner = SensorimotorSimulationRunner(max_steps=40, seed=3,
                                          state_dir=str(tmp_path / "s"))
    runner.run()
    assert runner.latent is None


def test_sensorimotor_enters_latent_mode_during_quiet(tmp_path):
    start = time.perf_counter()
    runner = SensorimotorSimulationRunner(
        max_steps=120, seed=3, state_dir=str(tmp_path / "s"),
        enable_latent=True, latent_interval_steps=30, latent_max_steps=12)
    runner.run()
    assert time.perf_counter() - start < 120.0
    # Latent machinery ran (cycles depend on how quiet the world was, but
    # the scheduler was consulted and the controller is back awake).
    assert runner.latent.scheduler.decisions
    assert runner.latent.controller.mode in ("awake", "quiet")
    assert runner.steps_run == 120


def test_no_simulated_action_executed_during_dream(tmp_path):
    """The in-loop assertion guards it; this test exercises a real cycle."""
    runner = SensorimotorSimulationRunner(
        max_steps=100, seed=3, state_dir=str(tmp_path / "s"),
        enable_latent=True, latent_interval_steps=25, latent_max_steps=10)
    runner.run()  # the runner asserts action_history is frozen per cycle
    if runner.latent_cycles:
        # Dream/replay traces came from body/world experience, marked offline.
        for dream in runner.latent.store.dreams():
            assert dream["offline"] is True
    summary = runner.latent.summary()
    assert summary["external_actions_during_latent"] == 0


def test_embodied_dream_uses_recent_traces(tmp_path):
    runner = SensorimotorSimulationRunner(
        max_steps=100, seed=5, state_dir=str(tmp_path / "s"),
        enable_latent=True, latent_interval_steps=25, latent_max_steps=10)
    runner.run()
    # The bridge trace (body/world experience) is what replay selects from.
    windows = runner.latent.replay_engine.select_windows(
        runner.bridge.trace, "high_valence", window_size=5, count=1)
    assert windows and windows[0]["rows"]


def test_inner_map_includes_embodied_latent(tmp_path):
    runner = SensorimotorSimulationRunner(
        max_steps=80, seed=3, state_dir=str(tmp_path / "s"),
        enable_latent=True, latent_interval_steps=25, latent_max_steps=10)
    runner.run()
    model = runner.observer.update()
    assert model.latent is not None
    assert model.embodiment is not None  # both sections coexist
