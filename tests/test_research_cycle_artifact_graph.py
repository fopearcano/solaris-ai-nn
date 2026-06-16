"""Research artifact graph: provenance chain, missing nodes, contradictions."""

from __future__ import annotations

from solaris_ai_nn.research_cycle import ArtifactEdgeType, ArtifactGraphBuilder


def _clean_bundle():
    return {
        "research_baseline": {"baseline_status": "validated"},
        "roadmap": {"x": 1},
        "architecture_evolution": {"x": 1},
        "experiment_compiler": {"x": 1},
        "implementation_intake": {"merge_recommendation_status": "recommend"},
        "post_merge": {"critical_regression_count": 0},
    }


def test_derived_from_chain_present():
    g = ArtifactGraphBuilder().build(_clean_bundle()).to_dict()
    derived = [(e["src"], e["dst"]) for e in g["edges"]
               if e["edge_type"] == ArtifactEdgeType.DERIVED_FROM]
    assert ("roadmap", "research_baseline_report") in derived
    assert ("post_merge_report", "implementation_intake_report") in derived


def test_missing_artifacts_are_missing_nodes():
    g = ArtifactGraphBuilder().build({"research_baseline": {"x": 1}}).to_dict()
    assert "post_merge_report" in g["missing_nodes"]


def test_falsifies_and_safety_blocks_visible():
    g = ArtifactGraphBuilder().build({
        "architecture_evolution": {"x": 1},
        "implementation_intake": {
            "merge_recommendation_status": "block_merge_due_to_safety"},
        "falsification": {"falsified_claim_count": 1}}).to_dict()
    types = {e["edge_type"] for e in g["edges"]}
    assert ArtifactEdgeType.FALSIFIES in types
    assert ArtifactEdgeType.SAFETY_BLOCKS in types
    assert g["artifact_graph_contradiction_count"] >= 1


def test_explicit_contradiction_preserved():
    g = ArtifactGraphBuilder().build({
        "research_baseline": {"x": 1},
        "contradictions": [{"src": "a", "dst": "b", "detail": "conflict"}],
    }).to_dict()
    assert any(e["edge_type"] == ArtifactEdgeType.CONTRADICTS
               for e in g["edges"])


def test_operator_confirmed_edge():
    g = ArtifactGraphBuilder().build({
        "research_baseline": {"x": 1},
        "operator_decisions": [
            {"decision_type": "confirm_external_merge", "status": "approved"}],
    }).to_dict()
    assert any(e["edge_type"] == ArtifactEdgeType.OPERATOR_CONFIRMED
               for e in g["edges"])
