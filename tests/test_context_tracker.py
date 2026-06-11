"""Tests for the ContextTracker."""

from __future__ import annotations

from solaris_ai_nn.world_model.context import CONTEXTS, ContextTracker
from solaris_ai_nn.world_model.graph import KnowledgeGraph
from solaris_ai_nn.world_model.nodes import NodeType


def test_current_context_from_snapshot():
    tracker = ContextTracker()
    assert tracker.current_context({}) == ["awake"]
    contexts = tracker.current_context({
        "latent": {"mode": "dream", "mysterium_pressure": 0.7},
        "embodiment": {"body": True},
        "energy_low": True,
        "logos_fracture": 0.6,
    })
    assert set(contexts) == {"dream", "embodied_gridworld",
                             "high_mysterium", "low_energy",
                             "high_logos_fracture"}
    assert tracker.current_context(
        {"latent": {"mode": "consolidation"}}) == ["sleep"]


def test_context_history_records_transitions():
    tracker = ContextTracker()
    entered = tracker.observe_context_change(["sleep", "high_mysterium"])
    assert set(entered) == {"sleep", "high_mysterium"}
    tracker.observe_context_change(["awake"])
    history = tracker.context_history()
    events = [(h["context"], h["event"]) for h in history]
    assert ("sleep", "entered") in events
    assert ("sleep", "left") in events
    assert ("awake", "entered") in events
    left = [h for h in history if h["event"] == "left"]
    assert all("duration_s" in h for h in left)


def test_unknown_contexts_ignored():
    tracker = ContextTracker()
    entered = tracker.observe_context_change(["awake", "hyperspace"])
    assert "hyperspace" not in entered
    assert "hyperspace" not in tracker.active


def test_update_graph_links_nodes_to_context():
    tracker = ContextTracker()
    tracker.observe_context_change(["embodied_gridworld"])
    graph = KnowledgeGraph()
    action = graph.upsert_node(NodeType.ACTION, "move_north")
    tracker.update_graph(graph, attach_node_ids=[action.node_id])
    context = graph.get_node(NodeType.CONTEXT, "embodied_gridworld")
    assert context is not None
    assert any(e.type == "belongs_to_context" for e in graph.edges.values())


def test_thirteen_contexts_defined():
    assert len(CONTEXTS) == 13
    data = ContextTracker().to_dict()
    assert data["known_contexts"] == list(CONTEXTS)
    assert "awake" in data["active"]
