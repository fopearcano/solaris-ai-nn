"""Tests for the executive inside the ContinuousRunner."""

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


def test_executive_disabled_by_default(tmp_path):
    runner = ContinuousRunner(state_dir=str(tmp_path / "s"), max_steps=30,
                              seed=3)
    runner.run()
    assert runner.executive is None
    assert "executive" not in runner.snapshot()
    assert not (tmp_path / "s" / "decision_trace.jsonl").exists()


def test_executive_runs_bounded(tmp_path):
    start = time.perf_counter()
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=120, seed=3,
        stimulus_provider=_provider(80),
        reaction_provider=lambda r, s: 1.0,
        enable_homeostasis=True, enable_executive=True,
        executive_report_interval_steps=40)
    runner.run()
    assert time.perf_counter() - start < 120.0
    summary = runner.snapshot()["executive"]
    assert summary["enabled"] is True
    assert summary["decisions"] > 0
    assert summary["selected_action_suggestion"] is not None
    assert runner.bridge.executive_layer is runner.executive


def test_checkpoint_saves_executive_state(tmp_path):
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=120, seed=3,
        stimulus_provider=_provider(80),
        enable_homeostasis=True, enable_executive=True,
        executive_report_interval_steps=40)
    runner.run()
    assert (tmp_path / "s" / "executive_state.json").exists()
    assert (tmp_path / "s" / "decision_trace.jsonl").exists()


def test_executive_with_full_stack(tmp_path):
    """Executive + homeostasis + latent + world model coexist."""
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=120, seed=3,
        stimulus_provider=_provider(50),
        enable_homeostasis=True, enable_executive=True,
        enable_latent=True, latent_interval_steps=40,
        enable_world_model=True,
        executive_report_interval_steps=40)
    runner.run()
    snap = runner.snapshot()
    assert snap["executive"]["decisions"] > 0
    assert snap["latent"]["mode"] == "awake"
    assert snap["world_model"]["graph_node_count"] > 1
