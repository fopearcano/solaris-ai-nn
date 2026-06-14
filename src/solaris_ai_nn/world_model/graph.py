"""KnowledgeGraph -- a plain-dict graph of observed structure.

No graph library, no database: nodes and edges live in dictionaries with
deterministic ids (same type+label -> same node; same triple -> same edge),
so repeated observation accumulates instead of duplicating. Everything is
inspectable, serializable, and exportable to DOT/Mermaid with stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .edges import EdgeType, GraphEdge, edge_id_for
from .nodes import GraphNode, NodeType, node_id_for

# Pilot-3 simulated-embodiment edge/node kinds (Prompt 34). These are stored as
# a ``pilot3_kind`` metadata tag on an ordinary edge/node (with
# ``simulation_scoped=True``); they come from *simulated* action only and must
# never be promoted to a real-world edge. (The edge ``type`` stays a normal
# EdgeType such as CAUSES_CANDIDATE / PRODUCES / BLOCKED_BY.)
PILOT3_ACTION_EDGE_KINDS = (
    "simulated_action_edge",
    "simulated_consequence_edge",
    "blocked_action_edge",
)
PILOT3_AFFORDANCE_NODE_KIND = "affordance_node"
PILOT3_SANDBOX_CAUSAL_CANDIDATE = "sandbox_only_causal_candidate"


@dataclass
class KnowledgeGraph:
    """Observed symbols and relations, accumulated deterministically."""

    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: Dict[str, GraphEdge] = field(default_factory=dict)
    # source_node_id -> list of edge_ids (kept sorted for determinism).
    _out: Dict[str, List[str]] = field(default_factory=dict, repr=False)
    _in: Dict[str, List[str]] = field(default_factory=dict, repr=False)

    # -- nodes -----------------------------------------------------------------

    def upsert_node(self, node_type: str, label: str,
                    source_module: str = "",
                    **metadata: Any) -> GraphNode:
        """Create or fetch the node for (type, label); counts the observation."""
        node_id = node_id_for(node_type, label)
        node = self.nodes.get(node_id)
        if node is None:
            node = GraphNode(node_id=node_id, type=node_type,
                             label=str(label))
            self.nodes[node_id] = node
        node.observe(source_module=source_module, **metadata)
        return node

    def observe_node(self, node_id: str, source_module: str = "",
                     **metadata: Any) -> Optional[GraphNode]:
        node = self.nodes.get(node_id)
        if node is not None:
            node.observe(source_module=source_module, **metadata)
        return node

    # -- edges ------------------------------------------------------------------

    def upsert_edge(self, source: GraphNode | str, edge_type: str,
                    target: GraphNode | str, weight_delta: float = 1.0,
                    evidence: Any = None, offline: bool = False,
                    **metadata: Any) -> GraphEdge:
        """Create or strengthen the edge (source, type, target)."""
        source_id = source.node_id if isinstance(source, GraphNode) else source
        target_id = target.node_id if isinstance(target, GraphNode) else target
        if source_id not in self.nodes or target_id not in self.nodes:
            raise KeyError("both endpoints must exist before adding an edge")
        edge_id = edge_id_for(source_id, edge_type, target_id)
        edge = self.edges.get(edge_id)
        if edge is None:
            edge = GraphEdge(edge_id=edge_id, source_node_id=source_id,
                             target_node_id=target_id, type=edge_type)
            self.edges[edge_id] = edge
            self._out.setdefault(source_id, []).append(edge_id)
            self._out[source_id].sort()
            self._in.setdefault(target_id, []).append(edge_id)
            self._in[target_id].sort()
        edge.observe(weight_delta=weight_delta, evidence=evidence,
                     offline=offline, **metadata)
        return edge

    def observe_edge(self, edge_id: str, weight_delta: float = 1.0,
                     evidence: Any = None,
                     offline: bool = False) -> Optional[GraphEdge]:
        edge = self.edges.get(edge_id)
        if edge is not None:
            edge.observe(weight_delta=weight_delta, evidence=evidence,
                         offline=offline)
        return edge

    # -- queries ------------------------------------------------------------------

    def neighbors(self, node_id: str, edge_type: Optional[str] = None,
                  direction: str = "out",
                  ) -> List[Tuple[GraphEdge, GraphNode]]:
        """(edge, neighbor) pairs from/to ``node_id``, strongest first."""
        index = self._out if direction == "out" else self._in
        pairs: List[Tuple[GraphEdge, GraphNode]] = []
        for edge_id in index.get(node_id, []):
            edge = self.edges[edge_id]
            if edge_type is not None and edge.type != edge_type:
                continue
            other_id = (edge.target_node_id if direction == "out"
                        else edge.source_node_id)
            pairs.append((edge, self.nodes[other_id]))
        pairs.sort(key=lambda pair: (-pair[0].weight, pair[0].edge_id))
        return pairs

    def strongest_edges(self, limit: int = 20,
                        edge_type: Optional[str] = None) -> List[GraphEdge]:
        edges = [e for e in self.edges.values()
                 if edge_type is None or e.type == edge_type]
        edges.sort(key=lambda e: (-e.weight, e.edge_id))
        return edges[:limit]

    def weak_edges(self, threshold: float = 0.5) -> List[GraphEdge]:
        edges = [e for e in self.edges.values() if e.weight < threshold]
        edges.sort(key=lambda e: (e.weight, e.edge_id))
        return edges

    def find(self, label: Optional[str] = None,
             node_type: Optional[str] = None) -> List[GraphNode]:
        """Nodes matching a label substring and/or an exact type."""
        needle = str(label).lower() if label is not None else None
        out = [n for n in self.nodes.values()
               if (node_type is None or n.type == node_type)
               and (needle is None or needle in n.label.lower())]
        out.sort(key=lambda n: n.node_id)
        return out

    def get_node(self, node_type: str, label: str) -> Optional[GraphNode]:
        return self.nodes.get(node_id_for(node_type, label))

    def subgraph_by_context(self, context_label: str) -> "KnowledgeGraph":
        """The nodes/edges attached to one context node (a copy, not a view)."""
        context_id = node_id_for(NodeType.CONTEXT, context_label)
        keep = {context_id}
        for edge in self.edges.values():
            if edge.type == EdgeType.BELONGS_TO_CONTEXT \
                    and edge.target_node_id == context_id:
                keep.add(edge.source_node_id)
        sub = KnowledgeGraph()
        for node_id in sorted(keep):
            node = self.nodes.get(node_id)
            if node is not None:
                sub.nodes[node_id] = GraphNode.from_dict(node.to_dict())
        for edge in self.edges.values():
            if edge.source_node_id in keep and edge.target_node_id in keep:
                sub.edges[edge.edge_id] = GraphEdge.from_dict(edge.to_dict())
                sub._out.setdefault(edge.source_node_id, []).append(
                    edge.edge_id)
                sub._in.setdefault(edge.target_node_id, []).append(
                    edge.edge_id)
        return sub

    # -- removal (used only by the synthesis pruner) ---------------------------------

    def remove_edge(self, edge_id: str) -> Optional[GraphEdge]:
        edge = self.edges.pop(edge_id, None)
        if edge is not None:
            self._out.get(edge.source_node_id, []).remove(edge_id)
            self._in.get(edge.target_node_id, []).remove(edge_id)
        return edge

    def remove_node(self, node_id: str) -> Optional[GraphNode]:
        """Remove a node and every edge touching it."""
        node = self.nodes.pop(node_id, None)
        if node is None:
            return None
        for edge_id in list(self._out.get(node_id, [])) \
                + list(self._in.get(node_id, [])):
            self.remove_edge(edge_id)
        self._out.pop(node_id, None)
        self._in.pop(node_id, None)
        return node

    # -- counts / status ----------------------------------------------------------------

    def node_counts_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for node in self.nodes.values():
            counts[node.type] = counts.get(node.type, 0) + 1
        return dict(sorted(counts.items()))

    def edge_counts_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for edge in self.edges.values():
            counts[edge.type] = counts.get(edge.type, 0) + 1
        return dict(sorted(counts.items()))

    def evidence_ratio(self) -> Dict[str, int]:
        real = sum(e.observation_count for e in self.edges.values())
        offline = sum(e.offline_observation_count
                      for e in self.edges.values())
        return {"real": real, "offline": offline}

    # -- serialization --------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [self.nodes[k].to_dict() for k in sorted(self.nodes)],
            "edges": [self.edges[k].to_dict() for k in sorted(self.edges)],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeGraph":
        graph = cls()
        for row in data.get("nodes", []):
            node = GraphNode.from_dict(row)
            graph.nodes[node.node_id] = node
        for row in data.get("edges", []):
            edge = GraphEdge.from_dict(row)
            graph.edges[edge.edge_id] = edge
            graph._out.setdefault(edge.source_node_id, []).append(
                edge.edge_id)
            graph._in.setdefault(edge.target_node_id, []).append(
                edge.edge_id)
        for index in (graph._out, graph._in):
            for key in index:
                index[key].sort()
        return graph

    # -- exports (stdlib only) -----------------------------------------------------------

    def to_dot(self, max_edges: int = 200) -> str:
        lines = ["digraph world_model {", "  rankdir=LR;"]
        shown_edges = self.strongest_edges(limit=max_edges)
        shown_nodes = {e.source_node_id for e in shown_edges} \
            | {e.target_node_id for e in shown_edges} \
            | set(list(sorted(self.nodes))[:50])
        for node_id in sorted(shown_nodes):
            node = self.nodes[node_id]
            label = f"{node.label}\\n[{node.type}] n={node.observation_count}"
            lines.append(f'  "{node_id}" [label="{label}"];')
        for edge in shown_edges:
            lines.append(
                f'  "{edge.source_node_id}" -> "{edge.target_node_id}" '
                f'[label="{edge.type} w={edge.weight:.1f}"];')
        lines.append("}")
        return "\n".join(lines)

    def to_mermaid(self, max_edges: int = 100) -> str:
        def mid(node_id: str) -> str:
            return node_id.replace(":", "_").replace("|", "_")

        lines = ["flowchart LR"]
        shown = self.strongest_edges(limit=max_edges)
        node_ids = {e.source_node_id for e in shown} \
            | {e.target_node_id for e in shown}
        for node_id in sorted(node_ids):
            node = self.nodes[node_id]
            lines.append(f'  {mid(node_id)}["{node.label} ({node.type})"]')
        for edge in shown:
            lines.append(f"  {mid(edge.source_node_id)} -- {edge.type} --> "
                         f"{mid(edge.target_node_id)}")
        return "\n".join(lines)
