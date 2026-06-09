"""Tests for the Inner MAP state graph."""

from __future__ import annotations

from solaris_ai_nn.inner_map.state_graph import StateGraph, build_default_state_graph

EXPECTED_NODES = {
    "runtime", "reservoir", "readout", "memory", "habit", "synthesis",
    "telemetry", "continuity", "bridge", "boundaries", "tendencies", "unknown",
}


def test_default_graph_has_expected_nodes():
    g = build_default_state_graph()
    assert EXPECTED_NODES <= set(g.nodes)
    assert "inner_map" in g.nodes  # the observer node
    assert len(g.edges) > 0


def test_add_node_and_edge():
    g = StateGraph()
    g.add_node("a", "alpha")
    g.add_edge("a", "b", "links")
    assert "a" in g.nodes and "b" in g.nodes  # endpoint auto-created
    assert ("a", "b", "links") in g.edges


def test_to_dict_structure():
    g = build_default_state_graph()
    d = g.to_dict()
    assert "nodes" in d and "edges" in d
    assert any(n["name"] == "reservoir" for n in d["nodes"])
    assert any(e["label"] for e in d["edges"])


def test_to_dot_export():
    dot = build_default_state_graph().to_dot()
    assert dot.startswith("digraph")
    assert "->" in dot
    assert "reservoir" in dot


def test_to_mermaid_export():
    mer = build_default_state_graph().to_mermaid()
    assert mer.splitlines()[0] == "flowchart LR"
    assert "-->" in mer
    assert "reservoir" in mer
