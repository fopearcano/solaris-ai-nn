"""Tests for the graph node/edge primitives."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.world_model.edges import EdgeType, GraphEdge, edge_id_for
from solaris_ai_nn.world_model.nodes import (
    GraphNode,
    NodeType,
    node_id_for,
    slug,
)


def test_required_node_types_exist():
    required = {"stimulus_pattern", "signal_type", "entity", "object",
                "place", "action", "reaction", "habit", "boundary",
                "context", "state", "unknown", "self_reference",
                "latent_schema",
                # ego (Prompt 18)
                "perspective_context", "action_authority",
                "attribution_source",
                # proto-language (Prompt 22)
                "proto_symbol"}
    assert required == set(NodeType.ALL)


def test_required_edge_types_exist():
    required = {"co_occurs_with", "precedes", "causes_candidate",
                "reinforces", "inhibits", "belongs_to_context", "near",
                "inside", "blocked_by", "produces", "predicts",
                "contradicts", "unknown_relation", "self_boundary",
                # ego (Prompt 18)
                "operates_under", "holds_authority", "bounded_by",
                "separates_evidence", "attributed_to",
                # proto-language (Prompt 22)
                "grounded_in"}
    assert required == set(EdgeType.ALL)


def test_node_serializes():
    node = GraphNode(node_id=node_id_for(NodeType.ACTION, "approach"),
                     type=NodeType.ACTION, label="approach")
    node.observe(source_module="test", note="x")
    data = node.to_dict()
    json.dumps(data)
    for key in ("node_id", "type", "label", "created_at", "updated_at",
                "observation_count", "confidence", "source_modules",
                "metadata"):
        assert key in data, key
    clone = GraphNode.from_dict(data)
    assert clone.node_id == node.node_id
    assert clone.observation_count == 1
    assert 0 < clone.confidence < 1.0


def test_edge_serializes():
    edge = GraphEdge(edge_id=edge_id_for("a", EdgeType.PRODUCES, "b"),
                     source_node_id="a", target_node_id="b",
                     type=EdgeType.PRODUCES)
    edge.observe(weight_delta=1.0, evidence={"step": 3})
    data = edge.to_dict()
    json.dumps(data)
    for key in ("edge_id", "source_node_id", "target_node_id", "type",
                "weight", "confidence", "observation_count",
                "last_observed_at", "evidence_refs", "metadata"):
        assert key in data, key
    clone = GraphEdge.from_dict(data)
    assert clone.weight == 1.0
    assert clone.evidence_refs[0]["evidence"]["step"] == 3


def test_offline_evidence_counted_separately():
    edge = GraphEdge(edge_id="x", source_node_id="a", target_node_id="b",
                     type=EdgeType.UNKNOWN_RELATION)
    edge.observe(evidence={"real": True})
    edge.observe(evidence={"simulated": True}, offline=True)
    assert edge.observation_count == 1
    assert edge.offline_observation_count == 1
    # Offline never inflates confidence (which tracks real observations).
    assert edge.confidence == GraphEdge(
        edge_id="y", source_node_id="a", target_node_id="b",
        type=EdgeType.UNKNOWN_RELATION).observe().confidence


def test_unknown_types_rejected():
    with pytest.raises(ValueError):
        GraphNode(node_id="x", type="belief", label="x")
    with pytest.raises(ValueError):
        GraphEdge(edge_id="x", source_node_id="a", target_node_id="b",
                  type="proves")


def test_deterministic_ids():
    assert node_id_for(NodeType.ACTION, "Move North!") \
        == node_id_for(NodeType.ACTION, "Move North!")
    assert slug("Move North!") == "move_north"
    assert node_id_for(NodeType.ACTION, "a") != node_id_for(NodeType.STATE,
                                                            "a")
