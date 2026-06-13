"""Integration: graph hygiene against a real world-model graph."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration import AutoRegenerationEngine, RepairPolicy
from solaris_ai_nn.autoregeneration.repair_actions import (
    RepairActionType,
    make_repair,
)
from solaris_ai_nn.autoregeneration.repair_policy import RepairDecision
from solaris_ai_nn.world_model.builder import WorldModelBuilder
from solaris_ai_nn.world_model.edges import EdgeType
from solaris_ai_nn.world_model.nodes import NodeType


def _builder_with_edge(edge_type):
    builder = WorldModelBuilder()
    a = builder.graph.upsert_node(NodeType.UNKNOWN, "a")
    b = builder.graph.upsert_node(NodeType.UNKNOWN, "b")
    edge = builder.graph.upsert_edge(a, edge_type, b, weight_delta=2.0,
                                    evidence="observed")
    return builder, edge


def test_graph_hygiene_preserves_contradiction_evidence(tmp_path):
    builder, edge = _builder_with_edge(EdgeType.CONTRADICTS)
    engine = AutoRegenerationEngine(
        state_dir=tmp_path, policy=RepairPolicy(mode="safe_auto_repair"),
        world_model=builder)
    decision = RepairDecision(
        action=make_repair(RepairActionType.MARK_WORLD_EDGE_AMBIGUOUS,
                           target_ref=edge.edge_id),
        mode="safe_auto_repair", apply_allowed=True)
    result = engine._handle(decision, {"state_dir": str(tmp_path)})
    assert result.applied is True
    # Edge still present (not deleted) and evidence preserved.
    assert edge.edge_id in builder.graph.edges
    assert edge.evidence_refs
    assert edge.metadata.get("ambiguous") is True


def test_stale_edge_weakened_safely(tmp_path):
    builder, edge = _builder_with_edge(EdgeType.PREDICTS)
    weight_before = edge.weight
    engine = AutoRegenerationEngine(
        state_dir=tmp_path, policy=RepairPolicy(mode="safe_auto_repair"),
        world_model=builder)
    decision = RepairDecision(
        action=make_repair(RepairActionType.WEAKEN_CONTRADICTORY_EDGE,
                           target_ref=edge.edge_id),
        mode="safe_auto_repair", apply_allowed=True)
    engine._handle(decision, {"state_dir": str(tmp_path)})
    assert edge.weight < weight_before
    assert edge.edge_id in builder.graph.edges  # weakened, not deleted
