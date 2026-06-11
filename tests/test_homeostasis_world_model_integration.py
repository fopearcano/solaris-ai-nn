"""Tests for homeostasis fed by (and feeding) the world model."""

from __future__ import annotations

from solaris_ai_nn.homeostasis.needs import NeedType
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator
from solaris_ai_nn.world_model.builder import WorldModelBuilder


def test_world_unknown_ratio_feeds_reduce_uncertainty():
    regulator = HomeostaticRegulator()
    result = regulator.update({
        "world_model": {"graph_node_count": 10, "unknown_node_count": 7,
                        "graph_edge_count": 12}})
    need = result.need_state.by_type(NeedType.REDUCE_UNCERTAINTY)
    assert need is not None
    assert "world_unknown_ratio" in need.source_variables


def test_predicted_danger_feeds_avoid_danger():
    regulator = HomeostaticRegulator()
    result = regulator.update({
        "world_model": {"graph_node_count": 5, "unknown_node_count": 0,
                        "graph_edge_count": 4, "predicted_danger": True}})
    need = result.need_state.by_type(NeedType.AVOID_DANGER)
    assert need is not None
    danger = regulator.state.get("danger_proximity")
    assert danger.metadata["raw_value"] == "predicted by graph"


def test_graph_redundancy_feeds_prune_need():
    regulator = HomeostaticRegulator()
    result = regulator.update({
        "world_model": {"graph_node_count": 10, "unknown_node_count": 0,
                        "graph_edge_count": 55}})  # 5.5 edges per node
    assert result.need_state.by_type(NeedType.PRUNE_REDUNDANCY) is not None


def test_homeostasis_feeds_need_nodes_back():
    builder = WorldModelBuilder()
    regulator = HomeostaticRegulator(world_model=builder)
    regulator.update({"embodiment": {"energy": 0.8, "max_energy": 10.0,
                                     "exhausted": True,
                                     "dist_reward": 1.0}})
    need_nodes = builder.graph.find(label="need:")
    desire_nodes = builder.graph.find(label="desire:")
    assert need_nodes and desire_nodes
    # The energy-vs-reward conflict became a contradicts edge.
    contradicts = [e for e in builder.graph.edges.values()
                   if e.type == "contradicts"]
    assert contradicts
    assert contradicts[0].evidence_refs[0]["evidence"]["rule"] \
        == "energy_exhaustion"


def test_graph_predictions_never_execute():
    import inspect

    from solaris_ai_nn.homeostasis import regulation

    source = inspect.getsource(regulation)
    for forbidden in ("subprocess", ".act(", "body.act", "execute("):
        assert forbidden not in source, forbidden
