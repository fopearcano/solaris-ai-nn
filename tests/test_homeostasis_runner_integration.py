"""Tests for homeostasis inside the ContinuousRunner."""

from __future__ import annotations

import time

from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.signals import canonical as C


def _provider(active):
    def provider(step):
        if step <= active:
            return C.Stimulus(payload=f"p{step % 2}", intensity=0.5)
        return None
    return provider


def test_homeostasis_disabled_by_default(tmp_path):
    runner = ContinuousRunner(state_dir=str(tmp_path / "s"), max_steps=30,
                              seed=3)
    runner.run()
    assert runner.homeostasis is None
    assert "homeostasis" not in runner.snapshot()
    assert not (tmp_path / "s" / "need_trace.jsonl").exists()


def test_homeostasis_runs_bounded(tmp_path):
    start = time.perf_counter()
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=120, seed=3,
        stimulus_provider=_provider(80),
        reaction_provider=lambda r, s: 1.0,
        enable_homeostasis=True, homeostasis_update_interval_steps=10)
    runner.run()
    assert time.perf_counter() - start < 120.0
    summary = runner.snapshot()["homeostasis"]
    assert summary["enabled"] is True
    assert summary["updates"] >= 10
    assert summary["dominant_drive"] is not None
    # The bridge was wired for biasing.
    assert runner.bridge.enable_homeostasis is True
    assert runner.bridge.homeostatic_regulator is runner.homeostasis


def test_checkpoint_saves_homeostasis_state(tmp_path):
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=120, seed=3,
        stimulus_provider=_provider(80),
        enable_homeostasis=True,
        homeostasis_report_interval_steps=60)
    runner.run()
    for name in ("homeostasis_state.json", "need_trace.jsonl",
                 "auto_determination.json", "homeostasis_report.md",
                 "homeostasis_report.json"):
        assert (tmp_path / "s" / name).exists(), name


def test_reactions_feed_valence(tmp_path):
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=80, seed=3,
        stimulus_provider=_provider(80),
        reaction_provider=lambda r, s: -0.8,  # consistently negative
        enable_homeostasis=True, homeostasis_update_interval_steps=10)
    runner.run()
    assert runner.homeostasis.valence.rolling() < 0


def test_works_with_latent_and_world_model(tmp_path):
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=120, seed=3,
        stimulus_provider=_provider(50),
        enable_homeostasis=True, enable_latent=True,
        latent_interval_steps=40, enable_world_model=True)
    runner.run()
    summary = runner.snapshot()["homeostasis"]
    assert summary["updates"] > 0
    # Need structure reached the world-model graph.
    assert runner.world_model.graph.find(label="need:")
