"""Tests for the KnowledgeGraph."""

from __future__ import annotations

import pytest

from solaris_ai_nn.world_model.edges import EdgeType
from solaris_ai_nn.world_model.graph import KnowledgeGraph
from solaris_ai_nn.world_model.nodes import NodeType


def _graph():
    g = KnowledgeGraph()
    light = g.upsert_node(NodeType.STIMULUS_PATTERN, "light")
    noise = g.upsert_node(NodeType.STIMULUS_PATTERN, "noise")
    approach = g.upsert_node(NodeType.ACTION, "approach")
    withdraw = g.upsert_node(NodeType.ACTION, "withdraw")
    for _ in range(5):
        g.upsert_edge(light, EdgeType.PRODUCES, approach)
    g.upsert_edge(noise, EdgeType.PRODUCES, withdraw, weight_delta=0.2)
    return g, light, approach


def test_upsert_node_accumulates():
    g = KnowledgeGraph()
    first = g.upsert_node(NodeType.ACTION, "approach")
    second = g.upsert_node(NodeType.ACTION, "approach")
    assert first is second
    assert second.observation_count == 2
    assert len(g.nodes) == 1


def test_upsert_edge_accumulates_and_requires_endpoints():
    g, light, approach = _graph()
    edge = g.upsert_edge(light, EdgeType.PRODUCES, approach)
    assert edge.observation_count == 6
    assert len(g.edges) == 2
    with pytest.raises(KeyError):
        g.upsert_edge("missing:node", EdgeType.PRODUCES, approach.node_id)


def test_neighbors():
    g, light, approach = _graph()
    pairs = g.neighbors(light.node_id)
    assert pairs[0][1].label == "approach"
    incoming = g.neighbors(approach.node_id, direction="in")
    assert incoming[0][1].label == "light"
    assert g.neighbors(light.node_id,
                       edge_type=EdgeType.BLOCKED_BY) == []


def test_strongest_and_weak_edges():
    g, _, _ = _graph()
    strongest = g.strongest_edges(limit=1)
    assert strongest[0].weight == 5.0
    weak = g.weak_edges(threshold=0.5)
    assert len(weak) == 1
    assert weak[0].weight == 0.2


def test_find_and_counts():
    g, _, _ = _graph()
    assert len(g.find(node_type=NodeType.ACTION)) == 2
    assert g.find(label="ligh")[0].label == "light"
    assert g.node_counts_by_type() == {"action": 2, "stimulus_pattern": 2}
    assert g.edge_counts_by_type() == {"produces": 2}


def test_subgraph_by_context():
    g, light, _ = _graph()
    context = g.upsert_node(NodeType.CONTEXT, "awake")
    g.upsert_edge(light, EdgeType.BELONGS_TO_CONTEXT, context)
    sub = g.subgraph_by_context("awake")
    assert light.node_id in sub.nodes
    assert context.node_id in sub.nodes
    assert len(sub.nodes) == 2  # only context members


def test_round_trip():
    g, _, _ = _graph()
    clone = KnowledgeGraph.from_dict(g.to_dict())
    assert len(clone.nodes) == len(g.nodes)
    assert len(clone.edges) == len(g.edges)
    assert clone.strongest_edges(1)[0].weight == 5.0
    assert clone.neighbors(clone.find(label="light")[0].node_id)


def test_dot_and_mermaid_export():
    g, _, _ = _graph()
    dot = g.to_dot()
    assert dot.startswith("digraph world_model")
    assert "produces" in dot
    mermaid = g.to_mermaid()
    assert mermaid.startswith("flowchart LR")
    assert "-- produces -->" in mermaid


def test_remove_node_removes_edges():
    g, light, approach = _graph()
    g.remove_node(approach.node_id)
    assert approach.node_id not in g.nodes
    assert all(e.target_node_id != approach.node_id
               for e in g.edges.values())
