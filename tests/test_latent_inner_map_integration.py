"""Tests for latent state inside the Inner MAP."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_inner_map_includes_latent_state():
    observer = InnerMapObserver(latent={
        "enabled": True, "mode": "awake",
        "last_transition": {"from_mode": "dream", "to_mode":
                            "wake_transition"},
        "sleep_cycle_count": 2, "dream_cycle_count": 1, "replay_count": 3,
        "counterfactual_count": 2, "anticipation_accuracy": 0.8,
        "mysterium_pressure": 0.3, "mysterium_reasons": ["novelty"],
        "complexity_pressure": None, "consolidated_schema_count": 4,
        "latent_safety_status": "ok", "latent_report_path": None})
    model = observer.update()
    assert model.latent["mode"] == "awake"
    assert model.latent["mysterium_pressure"] == 0.3
    clone = InnerMapModel.from_dict(model.to_dict())
    assert clone.latent["sleep_cycle_count"] == 2


def test_latent_absent_when_disabled():
    assert InnerMapObserver().update().latent is None


def test_observer_picks_latent_from_runner(tmp_path):
    from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner

    runner = ContinuousRunner(state_dir=str(tmp_path / "s"), max_steps=30,
                              seed=3, enable_latent=True,
                              latent_interval_steps=0)  # never cycles
    runner.run()
    model = runner.observer.update()
    assert model.latent is not None  # picked up via the runner duck-typing
    assert model.latent["enabled"] is True


def test_state_graph_includes_latent_nodes():
    graph = build_default_state_graph()
    for node in ("sleep_wake_controller", "latent_scheduler", "sleep_cycle",
                 "dream_cycle", "offline_replay_engine",
                 "counterfactual_generator", "anticipation_tracker",
                 "mysterium_tracker", "complexity_pressure_monitor",
                 "latent_safety_validator"):
        assert node in graph.nodes, node
    edges = {(src, dst) for src, dst, _ in graph.edges}
    assert ("memory", "offline_replay_engine") in edges
    assert ("offline_replay_engine", "dream_cycle") in edges
    assert ("anticipation_tracker", "mysterium_tracker") in edges
    assert ("complexity_pressure_monitor", "latent_scheduler") in edges
    assert ("dream_cycle", "inner_map") in edges
    assert "latent_scheduler" in graph.to_mermaid()
