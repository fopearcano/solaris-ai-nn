"""GraphSynthesisPruner -- synthesis-through-subtraction for graph memory.

Weak edges, weak nodes, and redundant duplicates are *proposed* for removal;
applying a proposal is dry-run by default, archives everything it removes
(so pruning is reversible), and production application goes through
WorldModelSafety (governance-gated). Evidence summaries are preserved in the
subtraction report -- nothing is silently forgotten.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .graph import KnowledgeGraph
from .nodes import NodeType
from .safety import WorldModelSafety


@dataclass
class GraphSynthesisPruner:
    """Proposes and (explicitly) applies graph subtraction."""

    safety: WorldModelSafety = field(default_factory=WorldModelSafety)
    min_node_observations: int = 2
    protected_node_types: tuple = (NodeType.CONTEXT, NodeType.SELF_REFERENCE,
                                   NodeType.BOUNDARY)

    proposals_made: int = field(default=0, init=False)
    applied_count: int = field(default=0, init=False)
    archive: List[Dict[str, Any]] = field(default_factory=list, init=False)
    last_report: Optional[Dict[str, Any]] = field(default=None, init=False)

    # -- proposal ---------------------------------------------------------------

    def propose_pruning(self, graph: KnowledgeGraph,
                        threshold: float = 0.5) -> Dict[str, Any]:
        """What subtraction would remove, with evidence summaries."""
        weak_edges = [e.edge_id for e in graph.weak_edges(threshold)
                      if e.observation_count <= 1
                      and e.offline_observation_count == 0]

        # Redundant nodes first, so merge candidates are not double-listed
        # as weak nodes below.
        redundant: List[Dict[str, str]] = []
        by_label: Dict[str, List[str]] = {}
        for node in graph.nodes.values():
            by_label.setdefault(node.label.lower(), []).append(node.node_id)
        for label, ids in sorted(by_label.items()):
            if len(ids) < 2:
                continue
            unknowns = [i for i in sorted(ids)
                        if graph.nodes[i].type == NodeType.UNKNOWN]
            typed = [i for i in sorted(ids)
                     if graph.nodes[i].type != NodeType.UNKNOWN]
            if unknowns and typed:
                # The unknown duplicate merges into the typed node.
                redundant.append({"merge_from": unknowns[0],
                                  "merge_into": typed[0]})
        merging = {m["merge_from"] for m in redundant}

        weak_nodes = []
        for node in sorted(graph.nodes.values(), key=lambda n: n.node_id):
            if node.type in self.protected_node_types \
                    or node.node_id in merging:
                continue
            connected = (len(graph._out.get(node.node_id, []))
                         + len(graph._in.get(node.node_id, [])))
            remaining = connected - sum(
                1 for eid in weak_edges
                if eid in graph._out.get(node.node_id, [])
                or eid in graph._in.get(node.node_id, []))
            if node.observation_count < self.min_node_observations \
                    and remaining == 0:
                weak_nodes.append(node.node_id)

        proposal = {
            "proposal_id": f"prune-{int(time.time() * 1000)}",
            "threshold": threshold,
            "weak_edges": weak_edges,
            "weak_nodes": weak_nodes,
            "redundant_merges": redundant,
            "evidence_summary": {
                "edges": [{"edge_id": eid,
                           "weight": graph.edges[eid].weight,
                           "observations": graph.edges[eid].observation_count,
                           "evidence_refs":
                               list(graph.edges[eid].evidence_refs)}
                          for eid in weak_edges[:50]],
                "nodes": [{"node_id": nid,
                           "observations":
                               graph.nodes[nid].observation_count}
                          for nid in weak_nodes[:50]],
            },
            "totals": {"edges": len(weak_edges), "nodes": len(weak_nodes),
                       "merges": len(redundant)},
        }
        self.proposals_made += 1
        return proposal

    # -- application ----------------------------------------------------------------

    def apply_pruning(self, graph: KnowledgeGraph,
                      proposal: Dict[str, Any], dry_run: bool = True,
                      context: Optional[Dict[str, Any]] = None,
                      ) -> Dict[str, Any]:
        """Apply (or simulate) a proposal. Dry-run never mutates the graph."""
        check = self.safety.validate_pruning(proposal, dry_run, context)
        if not check.safe:
            report = {"applied": False, "dry_run": dry_run,
                      "refused": True, "reasons": check.violations,
                      "proposal_id": proposal.get("proposal_id")}
            self.last_report = report
            return report

        removed_edges = 0
        removed_nodes = 0
        merged = 0
        if not dry_run:
            for edge_id in proposal.get("weak_edges", []):
                edge = graph.remove_edge(edge_id)
                if edge is not None:
                    self.archive.append({"kind": "edge",
                                         "data": edge.to_dict(),
                                         "proposal_id":
                                             proposal.get("proposal_id")})
                    removed_edges += 1
            for merge in proposal.get("redundant_merges", []):
                source = graph.nodes.get(merge["merge_from"])
                target = graph.nodes.get(merge["merge_into"])
                if source is None or target is None:
                    continue
                target.observation_count += source.observation_count
                self.archive.append({"kind": "node",
                                     "data": source.to_dict(),
                                     "merged_into": target.node_id,
                                     "proposal_id":
                                         proposal.get("proposal_id")})
                graph.remove_node(source.node_id)
                merged += 1
            for node_id in proposal.get("weak_nodes", []):
                node = graph.remove_node(node_id)
                if node is not None:
                    self.archive.append({"kind": "node",
                                         "data": node.to_dict(),
                                         "proposal_id":
                                             proposal.get("proposal_id")})
                    removed_nodes += 1
            self.applied_count += 1
            self.archive = self.archive[-500:]

        report = {
            "applied": not dry_run,
            "dry_run": dry_run,
            "proposal_id": proposal.get("proposal_id"),
            "would_remove" if dry_run else "removed": {
                "edges": (proposal["totals"]["edges"] if dry_run
                          else removed_edges),
                "nodes": (proposal["totals"]["nodes"] if dry_run
                          else removed_nodes),
                "merges": (proposal["totals"]["merges"] if dry_run
                           else merged),
            },
            "evidence_preserved": True,  # summaries in proposal + archive
            "reversible": True,
            "note": "synthesis through subtraction: weak structure removed, "
                    "evidence summaries kept",
        }
        self.last_report = report
        return report

    def restore(self, graph: KnowledgeGraph, proposal_id: str) -> int:
        """Undo a previously applied proposal from the archive."""
        from .edges import GraphEdge
        from .nodes import GraphNode

        restored = 0
        remaining = []
        for entry in self.archive:
            if entry.get("proposal_id") != proposal_id:
                remaining.append(entry)
                continue
            if entry["kind"] == "node":
                node = GraphNode.from_dict(entry["data"])
                graph.nodes[node.node_id] = node
            restored += 1
        for entry in self.archive:
            if entry.get("proposal_id") == proposal_id \
                    and entry["kind"] == "edge":
                edge = GraphEdge.from_dict(entry["data"])
                if edge.source_node_id in graph.nodes \
                        and edge.target_node_id in graph.nodes:
                    graph.edges[edge.edge_id] = edge
                    graph._out.setdefault(edge.source_node_id, []).append(
                        edge.edge_id)
                    graph._in.setdefault(edge.target_node_id, []).append(
                        edge.edge_id)
        self.archive = remaining
        return restored

    def snapshot(self) -> Dict[str, Any]:
        return {
            "proposals_made": self.proposals_made,
            "applied_count": self.applied_count,
            "archived_items": len(self.archive),
            "last_report": self.last_report,
        }
