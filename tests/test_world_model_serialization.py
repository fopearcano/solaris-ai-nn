"""Tests for world-model serialization."""

from __future__ import annotations

import json

from solaris_ai_nn.world_model.edges import EdgeType
from solaris_ai_nn.world_model.graph import KnowledgeGraph
from solaris_ai_nn.world_model.nodes import NodeType
from solaris_ai_nn.world_model.serialization import (
    load_graph,
    load_graph_jsonl,
    save_graph,
    save_graph_exports,
    save_graph_jsonl,
)


def _graph():
    g = KnowledgeGraph()
    a = g.upsert_node(NodeType.STIMULUS_PATTERN, "light")
    b = g.upsert_node(NodeType.ACTION, "approach")
    for _ in range(3):
        g.upsert_edge(a, EdgeType.PRODUCES, b, evidence={"step": 1})
    return g


def test_save_load_graph_json(tmp_path):
    g = _graph()
    path = save_graph(g, tmp_path / "world_model.json")
    assert path.exists()
    loaded = load_graph(path)
    assert len(loaded.nodes) == 2
    assert loaded.strongest_edges(1)[0].observation_count == 3
    # Loading a missing file yields an empty graph, not an error.
    assert len(load_graph(tmp_path / "missing.json").nodes) == 0


def test_save_load_jsonl(tmp_path):
    g = _graph()
    paths = save_graph_jsonl(g, tmp_path / "nodes.jsonl",
                             tmp_path / "edges.jsonl")
    node_rows = [json.loads(line) for line in
                 (tmp_path / "nodes.jsonl").read_text().splitlines()]
    assert len(node_rows) == 2
    loaded = load_graph_jsonl(paths["nodes"], paths["edges"])
    assert len(loaded.edges) == 1
    assert loaded.neighbors(loaded.find(label="light")[0].node_id)


def test_export_dot_and_mermaid_files(tmp_path):
    paths = save_graph_exports(_graph(), tmp_path)
    for key in ("json", "nodes", "edges", "dot", "mermaid"):
        assert key in paths, key
    dot = (tmp_path / "world_model.dot").read_text()
    assert "digraph world_model" in dot
    mmd = (tmp_path / "world_model.mmd").read_text()
    assert "flowchart LR" in mmd
    assert (tmp_path / "world_model_nodes.jsonl").exists()
    assert (tmp_path / "world_model_edges.jsonl").exists()
