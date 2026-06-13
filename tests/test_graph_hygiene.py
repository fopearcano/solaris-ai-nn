"""Tests for world-model (graph) hygiene."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.graph_hygiene import (
    WorldModelHygieneManager,
)


def test_contradictory_edge_detected():
    mgr = WorldModelHygieneManager()
    detected = mgr.detect({"world_model": {
        "contradiction_edges": ["a|contradicts|b"]}})
    assert detected["contradiction_edges"] == ["a|contradicts|b"]


def test_edge_marked_ambiguous_and_hypothesis_requested():
    mgr = WorldModelHygieneManager()
    actions = mgr.propose({"world_model": {
        "contradiction_edges": ["a|contradicts|b"]}})
    assert any(a.action_type == "mark_world_edge_ambiguous" for a in actions)
    assert mgr.hypothesis_requests


def test_weak_edge_weakened():
    mgr = WorldModelHygieneManager()
    actions = mgr.propose({"world_model": {"weak_edges": ["x|predicts|y"]}})
    assert any(a.action_type == "weaken_contradictory_edge" for a in actions)


def test_evidence_preserved_via_real_graph():
    from solaris_ai_nn.world_model.builder import WorldModelBuilder
    from solaris_ai_nn.world_model.edges import EdgeType
    from solaris_ai_nn.world_model.nodes import NodeType

    builder = WorldModelBuilder()
    a = builder.graph.upsert_node(NodeType.UNKNOWN, "a")
    b = builder.graph.upsert_node(NodeType.UNKNOWN, "b")
    edge = builder.graph.upsert_edge(a, EdgeType.CONTRADICTS, b,
                                    weight_delta=2.0,
                                    evidence="observed conflict")
    mgr = WorldModelHygieneManager()
    ok = mgr.apply_to_graph(builder.graph, edge.edge_id, weaken=True)
    assert ok
    # Edge still exists (not deleted); evidence refs preserved; marked.
    assert edge.edge_id in builder.graph.edges
    assert edge.metadata.get("ambiguous") is True
    assert edge.evidence_refs  # contradiction evidence preserved
