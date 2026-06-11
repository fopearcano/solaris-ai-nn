"""Tests for developmental state inside the Inner MAP."""

from __future__ import annotations

from solaris_ai_nn.developmental.developmental_runtime import (
    DevelopmentalRuntime,
)
from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph


def test_inner_map_includes_developmental_state(tmp_path):
    runtime = DevelopmentalRuntime(
        state_dir=tmp_path / "dev", simulated_time=True,
        max_steps=60, consolidation_interval_steps=30, seed=3)
    runtime.run()
    model = InnerMapObserver(developmental=runtime).update()
    assert model.developmental is not None
    for key in ("enabled", "current_epoch", "developmental_age_hours",
                "memory_layers", "fossil_memory_count",
                "milestone_count", "last_milestone", "growth_status",
                "drift_status", "structural_change_score",
                "phase_transition_candidates",
                "developmental_report_path"):
        assert key in model.developmental, key
    clone = InnerMapModel.from_dict(model.to_dict())
    assert clone.developmental["enabled"] is True


def test_developmental_absent_when_disabled():
    assert InnerMapObserver().update().developmental is None


def test_state_graph_includes_developmental_nodes():
    graph = build_default_state_graph()
    for node in ("developmental_runtime", "developmental_clock",
                 "epoch_manager", "memory_layer_manager",
                 "consolidation_policy", "growth_monitor",
                 "long_run_drift_monitor", "milestone_registry",
                 "autobiographical_memory",
                 "phase_transition_detector"):
        assert node in graph.nodes, node
    edges = {(src, dst) for src, dst, _ in graph.edges}
    assert ("telemetry", "developmental_clock") in edges
    assert ("memory", "memory_layer_manager") in edges
    assert ("latent_scheduler", "consolidation_policy") in edges
    assert ("world_model_builder", "growth_monitor") in edges
    assert ("long_run_drift_monitor", "operational_supervisor") in edges
    assert ("milestone_registry", "memory_layer_manager") in edges
    assert ("developmental_runtime", "inner_map") in edges
    assert "developmental_runtime" in graph.to_mermaid()
