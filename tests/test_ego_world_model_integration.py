"""Tests for the ego layer feeding the world model graph."""

from __future__ import annotations

from solaris_ai_nn.ego.self_model import SelfModel
from solaris_ai_nn.world_model.graph import KnowledgeGraph


def _fed_graph(tmp_path):
    model = SelfModel(state_dir=tmp_path)
    model.update({"run_id": "r1"})
    model.classify_event({"source": "stream", "kind": "stream_line"})
    graph = KnowledgeGraph()
    model.update_world_model(graph)
    return model, graph


def test_self_reference_nodes_created(tmp_path):
    _, graph = _fed_graph(tmp_path)
    runtime = graph.get_node("self_reference", "solaris_ai_nn_runtime")
    assert runtime is not None
    assert "operational self-reference only" \
        in runtime.metadata.get("note", "")
    counts = graph.node_counts_by_type()
    assert counts["self_reference"] == 1
    assert counts["perspective_context"] == 1
    assert counts["action_authority"] == 1


def test_boundary_nodes_created(tmp_path):
    _, graph = _fed_graph(tmp_path)
    counts = graph.node_counts_by_type()
    assert counts["boundary"] >= 16
    edge_counts = graph.edge_counts_by_type()
    assert edge_counts["bounded_by"] >= 16
    assert edge_counts["operates_under"] == 1
    assert edge_counts["holds_authority"] == 1
    # The counterfactual boundary edge is marked offline.
    assert edge_counts.get("separates_evidence", 0) == 1


def test_attribution_source_nodes(tmp_path):
    _, graph = _fed_graph(tmp_path)
    node = graph.get_node("attribution_source", "observed_from_stream")
    assert node is not None
    assert graph.edge_counts_by_type().get("attributed_to", 0) >= 1


def test_no_personhood_claim(tmp_path):
    _, graph = _fed_graph(tmp_path)
    blob = str(graph.to_dict()).lower()
    for forbidden in ("personhood", "conscious", "sentient", "soul",
                      "is a person"):
        assert forbidden not in blob, forbidden


def test_feed_is_idempotent_per_structure(tmp_path):
    model, graph = _fed_graph(tmp_path)
    before = len(graph.nodes)
    model.update_world_model(graph)  # same structure: observed, not grown
    assert len(graph.nodes) == before
