"""Tests for proto-symbols inside the world model graph."""

from __future__ import annotations

from solaris_ai_nn.protolanguage.layer import ProtoLanguageLayer
from solaris_ai_nn.world_model.graph import KnowledgeGraph


def _fed(tmp_path):
    layer = ProtoLanguageLayer(state_dir=tmp_path)
    layer.process_context({
        "repeated_stimulus_patterns": {"light_noise": 5},
        "mysterium_spikes": {"prediction_miss": 3}})
    graph = KnowledgeGraph()
    added = layer.update_world_model(graph)
    return layer, graph, added


def test_symbol_node_created(tmp_path):
    layer, graph, added = _fed(tmp_path)
    assert added["nodes"] >= 2
    counts = graph.node_counts_by_type()
    assert counts["proto_symbol"] == 2
    token = list(layer.registry.symbols.values())[0].token
    node = graph.get_node("proto_symbol", token)
    assert node is not None
    assert "not language understanding" in node.metadata.get("note", "")


def test_grounding_edge_created(tmp_path):
    _, graph, added = _fed(tmp_path)
    assert added["edges"] >= 2
    edge_counts = graph.edge_counts_by_type()
    assert edge_counts["grounded_in"] >= 2


def test_ambiguity_represented(tmp_path):
    layer, _, _ = _fed(tmp_path)
    symbol = list(layer.registry.symbols.values())[0]
    layer.registry.mark_ambiguous(symbol.symbol_id, "scattered")
    graph = KnowledgeGraph()
    layer.update_world_model(graph)
    node = graph.get_node("proto_symbol", symbol.token)
    assert node.metadata["ambiguity"] >= 0.7
    assert node.metadata["stable"] is False


def test_no_personhood_in_symbol_nodes(tmp_path):
    _, graph, _ = _fed(tmp_path)
    blob = str(graph.to_dict()).lower()
    for forbidden in ("understands", "speaks", "conscious",
                      "personhood"):
        assert forbidden not in blob.replace(
            "not language understanding", ""), forbidden
