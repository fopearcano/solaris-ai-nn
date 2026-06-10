"""Tests for latent cognition inside the ContinuousRunner."""

from __future__ import annotations

import time

from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.signals import canonical as C


def _provider(active_steps):
    def provider(step):
        if step <= active_steps:
            return C.Stimulus(payload=f"p{step % 3}", intensity=0.5)
        return None
    return provider


def test_latent_disabled_by_default(tmp_path):
    runner = ContinuousRunner(state_dir=str(tmp_path / "s"), max_steps=30,
                              seed=3)
    runner.run()
    assert runner.latent is None
    assert "latent" not in runner.snapshot()
    assert not (tmp_path / "s" / "latent_report.md").exists()


def test_latent_enabled_runs_bounded(tmp_path):
    start = time.perf_counter()
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=160, seed=3,
        stimulus_provider=_provider(50),
        reaction_provider=lambda r, s: 1.0 if r["suggested_action"] == "approach" else -0.5,
        enable_latent=True, latent_interval_steps=40, latent_max_steps=15)
    runner.run()
    assert time.perf_counter() - start < 120.0  # bounded, no infinite loop
    assert runner.telemetry.steps == 160
    latent = runner.snapshot()["latent"]
    assert latent["enabled"] is True
    assert latent["mode"] == "awake"  # always woken before the run ends
    assert latent["sleep_cycle_count"] >= 1
    assert latent["external_actions_during_latent"] == 0


def test_latent_report_saved(tmp_path):
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=160, seed=3,
        stimulus_provider=_provider(50),
        enable_latent=True, latent_interval_steps=40, latent_max_steps=15)
    runner.run()
    md = tmp_path / "s" / "latent_report.md"
    assert md.exists()
    text = md.read_text()
    assert "Latent cognition report" in text
    assert "Limitations and Unknowns" in text
    assert "not human-like sleep" in text or "no human-like sleep" in text
    assert (tmp_path / "s" / "latent_report.json").exists()
    assert (tmp_path / "s" / "latent_memory.jsonl").exists()


def test_latent_cycle_logged_to_continuity(tmp_path):
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=160, seed=3,
        stimulus_provider=_provider(40),
        enable_latent=True, latent_interval_steps=40, latent_max_steps=15)
    runner.run()
    from solaris_ai_nn.runtime.persistence import read_jsonl

    rows = list(read_jsonl(runner.pm.continuity_log_path))
    latent_rows = [r for r in rows if r.get("event_type") == "latent_cycle"]
    assert latent_rows
    assert "latent cycle at step" in latent_rows[0]["message"]


def test_latent_dry_run_keeps_production_learning_clean(tmp_path):
    """Dry-run latent cycles never apply replay learning to production."""
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=160, seed=3,
        stimulus_provider=_provider(50),
        enable_latent=True, latent_interval_steps=40, latent_max_steps=15,
        latent_dry_run=True)
    runner.run()
    assert runner.latent.dream_cycle.allow_production_mutation is False
    for cycle in runner.latent.store.cycles():
        if cycle["cycle_type"] == "dream":
            assert cycle["production_mutated"] is False


def test_inner_map_carries_latent_state(tmp_path):
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=160, seed=3,
        stimulus_provider=_provider(50),
        enable_latent=True, latent_interval_steps=40, latent_max_steps=15)
    runner.run()
    model = runner.observer.update()
    assert model.latent is not None
    assert model.latent["enabled"] is True
    assert "mysterium_pressure" in model.latent
