"""Tests for the GraphSynthesisPruner."""

from __future__ import annotations

from solaris_ai_nn.world_model.edges import EdgeType
from solaris_ai_nn.world_model.graph import KnowledgeGraph
from solaris_ai_nn.world_model.nodes import NodeType
from solaris_ai_nn.world_model.pruning import GraphSynthesisPruner


def _graph_with_weak_structure():
    g = KnowledgeGraph()
    strong_a = g.upsert_node(NodeType.STIMULUS_PATTERN, "light")
    strong_b = g.upsert_node(NodeType.ACTION, "approach")
    for _ in range(10):
        g.upsert_edge(strong_a, EdgeType.PRODUCES, strong_b)
    weak_a = g.upsert_node(NodeType.STIMULUS_PATTERN, "one_off")
    weak_b = g.upsert_node(NodeType.STATE, "transient")
    g.upsert_edge(weak_a, EdgeType.CO_OCCURS_WITH, weak_b, weight_delta=0.1)
    g.upsert_node(NodeType.UNKNOWN, "light")  # redundant duplicate
    return g


def test_proposes_weak_edge_pruning():
    g = _graph_with_weak_structure()
    pruner = GraphSynthesisPruner()
    proposal = pruner.propose_pruning(g, threshold=0.5)
    assert proposal["totals"]["edges"] == 1
    assert proposal["totals"]["nodes"] == 2  # both ends of the weak edge
    assert proposal["totals"]["merges"] == 1
    # Evidence summaries travel with the proposal.
    assert proposal["evidence_summary"]["edges"][0]["weight"] == 0.1


def test_dry_run_does_not_mutate_graph():
    g = _graph_with_weak_structure()
    nodes_before, edges_before = len(g.nodes), len(g.edges)
    pruner = GraphSynthesisPruner()
    proposal = pruner.propose_pruning(g)
    report = pruner.apply_pruning(g, proposal, dry_run=True)
    assert report["dry_run"] is True
    assert report["applied"] is False
    assert "would_remove" in report
    assert len(g.nodes) == nodes_before
    assert len(g.edges) == edges_before
    assert pruner.applied_count == 0


def test_production_pruning_requires_explicit_permission():
    g = _graph_with_weak_structure()
    pruner = GraphSynthesisPruner()
    proposal = pruner.propose_pruning(g)
    # Without permission, the safety gate refuses.
    refused = pruner.apply_pruning(g, proposal, dry_run=False)
    assert refused.get("refused") is True
    assert len(g.edges) == 2  # untouched
    # With the explicit flag it applies (governance gate at higher layers).
    applied = pruner.apply_pruning(g, proposal, dry_run=False,
                                   context={"pruning_allowed": True})
    assert applied["applied"] is True
    assert applied["removed"]["edges"] == 1
    assert applied["removed"]["merges"] == 1
    assert len(g.edges) == 1  # only the strong edge survives


def test_pruning_is_reversible():
    g = _graph_with_weak_structure()
    pruner = GraphSynthesisPruner()
    proposal = pruner.propose_pruning(g)
    nodes_before = len(g.nodes)
    pruner.apply_pruning(g, proposal, dry_run=False,
                         context={"pruning_allowed": True})
    assert len(g.nodes) < nodes_before
    restored = pruner.restore(g, proposal["proposal_id"])
    assert restored > 0
    # The weak nodes are back (the merge re-adds the unknown duplicate too).
    assert g.get_node(NodeType.STIMULUS_PATTERN, "one_off") is not None


def test_evidence_logs_never_deleted():
    g = _graph_with_weak_structure()
    pruner = GraphSynthesisPruner()
    proposal = pruner.propose_pruning(g)
    proposal["delete_trace_evidence"] = True
    report = pruner.apply_pruning(g, proposal, dry_run=False,
                                  context={"pruning_allowed": True})
    assert report.get("refused") is True
    assert any("trace evidence" in r for r in report["reasons"])


def test_protected_node_types_never_proposed():
    g = KnowledgeGraph()
    g.upsert_node(NodeType.CONTEXT, "awake")
    g.upsert_node(NodeType.SELF_REFERENCE, "solaris_ai_nn")
    g.upsert_node(NodeType.BOUNDARY, "grid_edge")
    proposal = GraphSynthesisPruner().propose_pruning(g)
    assert proposal["totals"]["nodes"] == 0
