"""Tests for the world model inside the ContinuousRunner."""

from __future__ import annotations

import time

from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner
from solaris_ai_nn.signals import canonical as C


def _provider(active):
    def provider(step):
        if step <= active:
            return C.Stimulus(payload=f"p{step % 3}", intensity=0.5)
        return None
    return provider


def test_world_model_disabled_by_default(tmp_path):
    runner = ContinuousRunner(state_dir=str(tmp_path / "s"), max_steps=30,
                              seed=3)
    runner.run()
    assert runner.world_model is None
    assert "world_model" not in runner.snapshot()
    assert not (tmp_path / "s" / "world_model.json").exists()


def test_world_model_enabled_runs_bounded(tmp_path):
    start = time.perf_counter()
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=100, seed=3,
        stimulus_provider=_provider(70),
        reaction_provider=lambda r, s: 1.0,
        enable_world_model=True, world_model_update_interval_steps=20)
    runner.run()
    assert time.perf_counter() - start < 120.0
    summary = runner.snapshot()["world_model"]
    assert summary["enabled"] is True
    assert summary["graph_node_count"] > 1
    assert summary["graph_edge_count"] > 0
    assert summary["strongest_association"] is not None


def test_checkpoint_saves_graph(tmp_path):
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=80, seed=3,
        stimulus_provider=_provider(60),
        enable_world_model=True)
    runner.run()
    for name in ("world_model.json", "world_model_nodes.jsonl",
                 "world_model_edges.jsonl", "world_model.dot",
                 "world_model.mmd", "world_model_report.md"):
        assert (tmp_path / "s" / name).exists(), name


def test_graph_restored_on_restart(tmp_path):
    first = ContinuousRunner(state_dir=str(tmp_path / "s"), max_steps=60,
                             seed=3, stimulus_provider=_provider(60),
                             enable_world_model=True)
    first.run()
    nodes_after_first = len(first.world_model.graph.nodes)
    second = ContinuousRunner(state_dir=str(tmp_path / "s"), max_steps=30,
                              seed=3, stimulus_provider=_provider(30),
                              enable_world_model=True)
    assert len(second.world_model.graph.nodes) == nodes_after_first
    second.run()  # continues accumulating on the restored graph
    light = second.world_model.graph.find(label="p0")
    assert light and light[0].observation_count > 0


def test_dry_run_pruning_during_run(tmp_path):
    runner = ContinuousRunner(
        state_dir=str(tmp_path / "s"), max_steps=120, seed=3,
        stimulus_provider=_provider(120),
        enable_world_model=True,
        world_model_update_interval_steps=20,
        world_model_pruning_interval_steps=60)
    runner.run()
    pruner = runner.world_model.pruner.snapshot()
    assert pruner["proposals_made"] >= 1
    assert pruner["applied_count"] == 0  # dry-run by default
    assert (pruner["last_report"] or {}).get("dry_run") is True
