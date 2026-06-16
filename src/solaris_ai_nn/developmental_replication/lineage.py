"""Developmental lineages -- experimental provenance, not biological ancestry.

A :class:`DevelopmentalLineage` records how runs relate as *experiments*: same
architecture, same/different seed, same/different sensorium, fixture->live,
control/ablation arms, restart continuations, branches from a checkpoint. This
is experimental provenance metadata. It is NOT biological ancestry; nothing here
is a parent, child, offspring, or descendant in any living sense.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LineageRelation:
    SAME_ARCHITECTURE = "same_architecture"
    SAME_SEED = "same_seed"
    DIFFERENT_SEED = "different_seed"
    SAME_SENSORIUM = "same_sensorium"
    DIFFERENT_SENSORIUM = "different_sensorium"
    FIXTURE_TO_LIVE = "fixture_to_live"
    CONTROL_ARM = "control_arm"
    ABLATION_ARM = "ablation_arm"
    RESTART_CONTINUATION = "restart_continuation"
    BRANCH_FROM_CHECKPOINT = "branch_from_checkpoint"
    UNKNOWN_RELATION = "unknown_relation"

    ALL = (SAME_ARCHITECTURE, SAME_SEED, DIFFERENT_SEED, SAME_SENSORIUM,
           DIFFERENT_SENSORIUM, FIXTURE_TO_LIVE, CONTROL_ARM, ABLATION_ARM,
           RESTART_CONTINUATION, BRANCH_FROM_CHECKPOINT, UNKNOWN_RELATION)


@dataclass
class LineageNode:
    """One run as a node in a lineage (provenance metadata only)."""

    run_id: str
    sensorium_profile: str = "unknown"
    seed: Optional[int] = None
    fixture_live_replay: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {"run_id": self.run_id,
                "sensorium_profile": self.sensorium_profile, "seed": self.seed,
                "fixture_live_replay": self.fixture_live_replay}


@dataclass
class LineageComparison:
    """A structural comparison between a parent and child lineage node."""

    parent_run: str
    child_run: str
    shared_checkpoints: List[str] = field(default_factory=list)
    divergent_modules: List[str] = field(default_factory=list)
    sensorium_differences: List[str] = field(default_factory=list)
    source_diet_differences: List[str] = field(default_factory=list)
    safety_differences: List[str] = field(default_factory=list)
    developmental_differences: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=lambda: [
        "experimental provenance, not biological ancestry"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parent_run": self.parent_run, "child_run": self.child_run,
            "shared_checkpoints": list(self.shared_checkpoints),
            "divergent_modules": list(self.divergent_modules),
            "sensorium_differences": list(self.sensorium_differences),
            "source_diet_differences": list(self.source_diet_differences),
            "safety_differences": list(self.safety_differences),
            "developmental_differences": list(self.developmental_differences),
            "limitations": list(self.limitations),
        }


@dataclass
class DevelopmentalLineage:
    """A directed-acyclic provenance graph over developmental runs."""

    lineage_id: str = "lineage"
    nodes: Dict[str, LineageNode] = field(default_factory=dict)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    comparisons: List[LineageComparison] = field(default_factory=list)

    def add_node(self, node: LineageNode) -> None:
        self.nodes[node.run_id] = node

    def relate(self, parent: str, child: str, relation: str, *,
               detail: str = "") -> Dict[str, Any]:
        if relation not in LineageRelation.ALL:
            relation = LineageRelation.UNKNOWN_RELATION
        edge = {"parent_run": parent, "child_run": child, "relation": relation,
                "detail": detail, "biological_ancestry": False}
        self.edges.append(edge)
        return edge

    def branch_from_checkpoint(self, parent: str, child: str, *,
                               checkpoint_id: str = "") -> Dict[str, Any]:
        """Record a checkpoint branch as metadata only (no artifact created)."""
        return self.relate(parent, child,
                           LineageRelation.BRANCH_FROM_CHECKPOINT,
                           detail=f"checkpoint={checkpoint_id} (metadata only)")

    def compare(self, parent: "RegisteredLike", child: "RegisteredLike",
                ) -> LineageComparison:
        comp = LineageComparison(parent_run=_rid(parent), child_run=_rid(child))
        if _attr(parent, "sensorium_profile") != _attr(child,
                                                        "sensorium_profile"):
            comp.sensorium_differences.append(
                f"{_attr(parent, 'sensorium_profile')} -> "
                f"{_attr(child, 'sensorium_profile')}")
        ps, cs = _attr(parent, "source_diet", {}), _attr(child, "source_diet",
                                                         {})
        for key in set(ps) | set(cs):
            if ps.get(key) != cs.get(key):
                comp.source_diet_differences.append(key)
        pd, cd = (_attr(parent, "developmental_profile", {}),
                  _attr(child, "developmental_profile", {}))
        if pd.get("structural_growth_status") != cd.get(
                "structural_growth_status"):
            comp.developmental_differences.append(
                f"growth: {pd.get('structural_growth_status')} -> "
                f"{cd.get('structural_growth_status')}")
        self.comparisons.append(comp)
        return comp

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lineage_id": self.lineage_id,
            "node_count": len(self.nodes),
            "nodes": {rid: n.to_dict() for rid, n in self.nodes.items()},
            "edges": list(self.edges),
            "comparisons": [c.to_dict() for c in self.comparisons],
            "note": ("experimental provenance, not biological ancestry; no run "
                     "is a parent, child, or offspring in any living sense"),
        }


# Light structural typing helpers (a registered run or a plain dict both work).
RegisteredLike = Any


def _rid(run: RegisteredLike) -> str:
    return getattr(run, "run_id", None) or (run.get("run_id")
                                            if isinstance(run, dict) else "?")


def _attr(run: RegisteredLike, name: str, default=None):
    if isinstance(run, dict):
        return run.get(name, default if default is not None else "unknown")
    return getattr(run, name, default if default is not None else "unknown")
