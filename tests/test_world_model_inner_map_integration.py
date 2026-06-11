"""Tests for world-model state inside the Inner MAP."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import InnerMapModel
from solaris_ai_nn.inner_map.observer import InnerMapObserver
from solaris_ai_nn.inner_map.state_graph import build_default_state_graph
from solaris_ai_nn.world_model.builder import WorldModelBuilder


def test_inner_map_includes_world_model_summary():
    builder = WorldModelBuilder()
    builder.update_from_reaction("approach", 1.0)
    model = InnerMapObserver(world_model=builder).update()
    assert model.world_model is not None
    assert model.world_model["enabled"] is True
    assert model.world_model["graph_node_count"] > 1
    clone = InnerMapModel.from_dict(model.to_dict())
    assert clone.world_model["graph_edge_count"] \
        == model.world_model["graph_edge_count"]


def test_world_model_absent_when_disabled():
    assert InnerMapObserver().update().world_model is None


def test_observer_picks_world_model_from_runner(tmp_path):
    from solaris_ai_nn.runtime.continuous_runner import ContinuousRunner

    runner = ContinuousRunner(state_dir=str(tmp_path / "s"), max_steps=30,
                              seed=3, enable_world_model=True)
    runner.run()
    model = runner.observer.update()
    assert model.world_model is not None  # via runner duck-typing


def test_state_graph_includes_world_model_nodes():
    graph = build_default_state_graph()
    for node in ("knowledge_graph", "world_model_builder",
                 "signal_graph_extractor", "embodiment_graph_extractor",
                 "language_graph_extractor", "latent_graph_extractor",
                 "association_learner", "causal_association_model",
                 "context_tracker", "world_model_predictor",
                 "graph_synthesis_pruner"):
        assert node in graph.nodes, node
    edges = {(src, dst) for src, dst, _ in graph.edges}
    assert ("memory", "world_model_builder") in edges
    assert ("language_layer", "world_model_builder") in edges
    assert ("simulated_body", "world_model_builder") in edges
    assert ("dream_cycle", "world_model_builder") in edges
    assert ("world_model_predictor", "anticipation_tracker") in edges
    assert ("world_model_builder", "inner_map") in edges
    assert ("graph_synthesis_pruner", "knowledge_graph") in edges
    assert "world_model_builder" in graph.to_mermaid()
