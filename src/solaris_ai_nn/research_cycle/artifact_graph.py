"""Research artifact graph -- evidence provenance, not cognition.

:class:`ResearchArtifactGraph` records the artifacts of a cycle and the relations
between them (derived_from, validates, blocks, supersedes, contradicts, supports,
requires, missing_for, operator_confirmed, safety_blocks, falsifies). It is
evidence provenance: contradictions stay visible, missing required artifacts
appear as missing nodes, and conflicting evidence is never collapsed into a score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ArtifactNodeType:
    BASELINE_REPORT = "baseline_report"
    ROADMAP = "roadmap"
    ARCHITECTURE_EVOLUTION_REPORT = "architecture_evolution_report"
    BRANCH_MANIFEST = "branch_manifest"
    PROMPT_PACK = "prompt_pack"
    BRANCH_SPEC = "branch_spec"
    TEST_MATRIX = "test_matrix"
    IMPLEMENTATION_INTAKE_REPORT = "implementation_intake_report"
    DIFF_AUDIT = "diff_audit"
    SAFETY_AUDIT = "safety_audit"
    MERGE_RECOMMENDATION = "merge_recommendation"
    POST_MERGE_REPORT = "post_merge_report"
    BASELINE_REGISTRY = "baseline_registry"
    RESEARCH_BASELINE_REPORT = "research_baseline_report"
    SOAK_DOSSIER = "soak_dossier"
    REPLICATION_REPORT = "replication_report"
    FALSIFICATION_REPORT = "falsification_report"
    SAFETY_INVARIANT_REPORT = "safety_invariant_report"
    OPERATOR_NOTE = "operator_note"
    UNKNOWN = "unknown"

    ALL = (BASELINE_REPORT, ROADMAP, ARCHITECTURE_EVOLUTION_REPORT,
           BRANCH_MANIFEST, PROMPT_PACK, BRANCH_SPEC, TEST_MATRIX,
           IMPLEMENTATION_INTAKE_REPORT, DIFF_AUDIT, SAFETY_AUDIT,
           MERGE_RECOMMENDATION, POST_MERGE_REPORT, BASELINE_REGISTRY,
           RESEARCH_BASELINE_REPORT, SOAK_DOSSIER, REPLICATION_REPORT,
           FALSIFICATION_REPORT, SAFETY_INVARIANT_REPORT, OPERATOR_NOTE,
           UNKNOWN)


class ArtifactEdgeType:
    DERIVED_FROM = "derived_from"
    VALIDATES = "validates"
    BLOCKS = "blocks"
    SUPERSEDES = "supersedes"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    REQUIRES = "requires"
    MISSING_FOR = "missing_for"
    OPERATOR_CONFIRMED = "operator_confirmed"
    SAFETY_BLOCKS = "safety_blocks"
    FALSIFIES = "falsifies"
    UNKNOWN_RELATION = "unknown_relation"

    ALL = (DERIVED_FROM, VALIDATES, BLOCKS, SUPERSEDES, CONTRADICTS, SUPPORTS,
           REQUIRES, MISSING_FOR, OPERATOR_CONFIRMED, SAFETY_BLOCKS, FALSIFIES,
           UNKNOWN_RELATION)


@dataclass
class ArtifactNode:
    """One artifact node (present or missing)."""

    node_id: str
    node_type: str
    present: bool = True
    ref: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "node_type": self.node_type,
                "present": self.present, "ref": self.ref}


@dataclass
class ArtifactEdge:
    """One directed relation between two artifact nodes."""

    src: str
    dst: str
    edge_type: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"src": self.src, "dst": self.dst, "edge_type": self.edge_type,
                "detail": self.detail}


@dataclass
class ResearchArtifactGraph:
    """An evidence-provenance graph; contradictions stay visible."""

    nodes: Dict[str, ArtifactNode] = field(default_factory=dict)
    edges: List[ArtifactEdge] = field(default_factory=list)

    def add_node(self, node_id: str, node_type: str, *, present: bool = True,
                 ref: str = "") -> None:
        if node_type not in ArtifactNodeType.ALL:
            node_type = ArtifactNodeType.UNKNOWN
        self.nodes[node_id] = ArtifactNode(node_id=node_id, node_type=node_type,
                                           present=present, ref=ref)

    def add_edge(self, src: str, dst: str, edge_type: str, *,
                 detail: str = "") -> None:
        if edge_type not in ArtifactEdgeType.ALL:
            edge_type = ArtifactEdgeType.UNKNOWN_RELATION
        self.edges.append(ArtifactEdge(src=src, dst=dst, edge_type=edge_type,
                                       detail=detail))

    @property
    def missing_nodes(self) -> List[str]:
        return [n.node_id for n in self.nodes.values() if not n.present]

    @property
    def contradiction_count(self) -> int:
        return sum(1 for e in self.edges
                   if e.edge_type in (ArtifactEdgeType.CONTRADICTS,
                                      ArtifactEdgeType.FALSIFIES))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_graph_node_count": len(self.nodes),
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": [e.to_dict() for e in self.edges],
            "edge_count": len(self.edges),
            "missing_nodes": self.missing_nodes,
            "artifact_graph_contradiction_count": self.contradiction_count,
            "note": "evidence provenance, not cognition; contradictions and "
                    "missing nodes stay visible and conflicting evidence is "
                    "never collapsed into a single score",
        }


@dataclass
class ArtifactGraphBuilder:
    """Builds the artifact graph from the cycle evidence bundle."""

    # (bundle key, node id, node type) for the canonical cycle artifacts.
    _NODES = (
        ("research_baseline", "research_baseline_report",
         ArtifactNodeType.RESEARCH_BASELINE_REPORT),
        ("roadmap", "roadmap", ArtifactNodeType.ROADMAP),
        ("architecture_evolution", "architecture_evolution_report",
         ArtifactNodeType.ARCHITECTURE_EVOLUTION_REPORT),
        ("experiment_compiler", "prompt_pack", ArtifactNodeType.PROMPT_PACK),
        ("implementation_intake", "implementation_intake_report",
         ArtifactNodeType.IMPLEMENTATION_INTAKE_REPORT),
        ("post_merge", "post_merge_report", ArtifactNodeType.POST_MERGE_REPORT),
        ("soak", "soak_dossier", ArtifactNodeType.SOAK_DOSSIER),
        ("replication", "replication_report",
         ArtifactNodeType.REPLICATION_REPORT),
        ("falsification", "falsification_report",
         ArtifactNodeType.FALSIFICATION_REPORT),
    )
    # Provenance chain (downstream derived_from upstream).
    _CHAIN = ("research_baseline_report", "roadmap",
              "architecture_evolution_report", "prompt_pack",
              "implementation_intake_report", "post_merge_report")

    def build(self, bundle: Dict[str, Any]) -> ResearchArtifactGraph:
        bundle = bundle or {}
        graph = ResearchArtifactGraph()
        for key, node_id, node_type in self._NODES:
            graph.add_node(node_id, node_type, present=bool(bundle.get(key)),
                           ref=key)
        # derived_from chain (only between present nodes).
        present_chain = [n for n in self._CHAIN
                         if graph.nodes[n].present]
        for downstream, upstream in zip(present_chain[1:], present_chain[:-1]):
            graph.add_edge(downstream, upstream,
                           ArtifactEdgeType.DERIVED_FROM)

        intake = bundle.get("implementation_intake", {}) or {}
        pm = bundle.get("post_merge", {}) or {}

        # safety_blocks / blocks edges from intake/post-merge status.
        if str(intake.get("merge_recommendation_status", "")).startswith(
                "block_merge_due_to_safety"):
            graph.add_edge("safety_audit", "implementation_intake_report",
                           ArtifactEdgeType.SAFETY_BLOCKS,
                           detail="intake blocked by safety")
            graph.add_node("safety_audit", ArtifactNodeType.SAFETY_AUDIT)
        if int(pm.get("critical_regression_count", 0) or 0) > 0:
            graph.add_edge("post_merge_report", "research_baseline_report",
                           ArtifactEdgeType.BLOCKS,
                           detail="critical regression blocks baseline")

        # falsifies / contradicts edge from a falsification report.
        fals = bundle.get("falsification", {}) or {}
        if int(fals.get("falsified_claim_count", 0) or 0) > 0:
            graph.add_edge("falsification_report",
                           "architecture_evolution_report",
                           ArtifactEdgeType.FALSIFIES,
                           detail="falsified claim(s) present")

        # Explicit contradictions supplied in the bundle stay visible.
        for c in bundle.get("contradictions", []) or []:
            graph.add_edge(c.get("src", "unknown"), c.get("dst", "unknown"),
                           ArtifactEdgeType.CONTRADICTS,
                           detail=c.get("detail", ""))

        # operator_confirmed edges.
        for dec in bundle.get("operator_decisions", []) or []:
            if dec.get("status") == "approved":
                graph.add_node("operator_note", ArtifactNodeType.OPERATOR_NOTE)
                graph.add_edge("operator_note", "research_baseline_report",
                               ArtifactEdgeType.OPERATOR_CONFIRMED,
                               detail=dec.get("decision_type", ""))
                break
        return graph
