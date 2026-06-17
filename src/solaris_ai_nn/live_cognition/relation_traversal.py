"""Live relation traversal -- bounded walks over the private syntax graph.

:class:`LiveRelationTraversal` walks the Prompt 70 private syntax graph from sign to
sign / concept / source within a bounded depth. Traversal is bounded, never invents
relations, and does not imply reasoning or understanding; weak relations stay weak
and contaminated/blocked relations are not traversed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class TraversalStatus:
    OK = "ok"
    TRUNCATED_BY_DEPTH = "truncated_by_depth"
    EMPTY = "empty"
    UNKNOWN = "unknown"

    ALL = (OK, TRUNCATED_BY_DEPTH, EMPTY, UNKNOWN)


@dataclass
class RelationTraversalPath:
    """One bounded path through the private syntax graph."""

    nodes: List[str] = field(default_factory=list)
    relation_types: List[str] = field(default_factory=list)
    strength: str = "weak"
    truncated: bool = False

    @property
    def depth(self) -> int:
        return max(0, len(self.nodes) - 1)

    def to_dict(self) -> Dict[str, Any]:
        return {"nodes": list(self.nodes),
                "relation_types": list(self.relation_types),
                "depth": self.depth, "strength": self.strength,
                "truncated": self.truncated, "implies_reasoning": False}


@dataclass
class LiveRelationTraversalResult:
    """The aggregate bounded-traversal result."""

    paths: List[RelationTraversalPath] = field(default_factory=list)
    status: str = TraversalStatus.UNKNOWN
    max_depth: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "traversal_status": self.status, "max_depth": self.max_depth,
            "path_count": len(self.paths),
            "max_observed_depth": max((p.depth for p in self.paths), default=0),
            "paths": [p.to_dict() for p in self.paths[:100]],
            "note": "traversal is bounded and depth-limited; it never invents "
                    "relations and does not imply reasoning or understanding; "
                    "weak relations stay weak",
        }


@dataclass
class LiveRelationTraversal:
    """Performs bounded, depth-limited traversal of the private syntax graph."""

    max_depth: int = 3
    max_paths: int = 100

    def traverse(self, private_syntax: Dict[str, Any],
                 ) -> LiveRelationTraversalResult:
        result = LiveRelationTraversalResult(max_depth=self.max_depth)
        relations = [r for r in (private_syntax.get("relations", []) or [])
                     if not r.get("blocked")]
        if not relations:
            result.status = TraversalStatus.EMPTY
            return result

        # Build a bounded adjacency (only non-blocked relations are traversable).
        adj: Dict[str, List[Dict[str, Any]]] = {}
        for r in relations:
            adj.setdefault(r.get("source_sign", ""), []).append(r)

        truncated_any = False
        for start in list(adj.keys()):
            path = RelationTraversalPath(nodes=[start])
            node = start
            seen = {start}
            while len(adj.get(node, [])) and path.depth < self.max_depth:
                # Deterministic: follow the first unseen edge.
                nxt = None
                for rel in adj.get(node, []):
                    target = rel.get("target_sign", "")
                    if target and target not in seen and target != "(none)":
                        nxt = rel
                        break
                if nxt is None:
                    break
                target = nxt.get("target_sign", "")
                path.nodes.append(target)
                path.relation_types.append(nxt.get("relation_type", ""))
                # Strength is the weakest along the path (stays weak).
                if nxt.get("strength") == "uncertain":
                    path.strength = "uncertain"
                seen.add(target)
                node = target
            if len(adj.get(node, [])) and path.depth >= self.max_depth:
                path.truncated = True
                truncated_any = True
            if path.depth >= 1:
                result.paths.append(path)
            if len(result.paths) >= self.max_paths:
                truncated_any = True
                break
        result.status = (TraversalStatus.TRUNCATED_BY_DEPTH if truncated_any
                         else TraversalStatus.OK)
        if not result.paths:
            result.status = TraversalStatus.EMPTY
        return result
