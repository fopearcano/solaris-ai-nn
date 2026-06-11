"""Context tracking -- which situation the observations belong to.

A context is a coarse, named situation (awake, embodied_gridworld,
high_mysterium, post_restart, ...). The tracker derives the active contexts
from a runtime snapshot, records transitions, and links graph structure to
context nodes so subgraphs stay separable by situation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .edges import EdgeType
from .graph import KnowledgeGraph
from .nodes import NodeType

CONTEXTS = (
    "awake", "quiet", "sleep", "replay", "dream",
    "embodied_gridworld", "pilot_stream", "solaris_sidecar",
    "high_mysterium", "low_energy", "high_logos_fracture",
    "post_restart", "post_plasticity",
)


@dataclass
class ContextState:
    """One active context with when it was entered."""

    name: str
    entered_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ContextTracker:
    """Derives, records, and graph-links the active contexts."""

    active: Dict[str, ContextState] = field(default_factory=lambda: {
        "awake": ContextState("awake")})
    history: List[Dict[str, Any]] = field(default_factory=list)
    max_history: int = 200

    def current_context(self, snapshot: Optional[Dict[str, Any]] = None,
                        ) -> List[str]:
        """Derive the active context names from a runtime snapshot."""
        snap = snapshot or {}
        contexts: List[str] = []
        mode = str((snap.get("latent") or {}).get("mode")
                   or snap.get("mode") or "awake")
        if mode in ("awake", "quiet", "sleep", "replay", "dream"):
            contexts.append(mode)
        elif mode in ("consolidation", "wake_transition"):
            contexts.append("sleep")
        if snap.get("embodiment") or snap.get("embodied"):
            contexts.append("embodied_gridworld")
        if snap.get("pilot_stream") or (snap.get("pilot") or {}).get(
                "pilot_profile") == "read_only_stream":
            contexts.append("pilot_stream")
        if snap.get("sidecar") or snap.get("integration"):
            contexts.append("solaris_sidecar")
        mysterium = float((snap.get("latent") or {}).get(
            "mysterium_pressure", snap.get("mysterium_pressure", 0.0)) or 0.0)
        if mysterium >= 0.6:
            contexts.append("high_mysterium")
        if snap.get("energy_low") or snap.get("exhausted"):
            contexts.append("low_energy")
        if float(snap.get("logos_fracture", 0.0) or 0.0) >= 0.5:
            contexts.append("high_logos_fracture")
        if snap.get("restart_count", 0) and snap.get("just_restarted"):
            contexts.append("post_restart")
        if snap.get("plasticity_applied"):
            contexts.append("post_plasticity")
        return contexts or ["awake"]

    def observe_context_change(self, contexts: List[str]) -> List[str]:
        """Record entering/leaving contexts; returns the newly entered ones."""
        wanted = {c for c in contexts if c in CONTEXTS}
        entered = []
        for name in sorted(wanted - set(self.active)):
            self.active[name] = ContextState(name)
            self.history.append({"context": name, "event": "entered",
                                 "timestamp": time.time()})
            entered.append(name)
        for name in sorted(set(self.active) - wanted):
            state = self.active.pop(name)
            self.history.append({"context": name, "event": "left",
                                 "timestamp": time.time(),
                                 "duration_s": round(
                                     time.time() - state.entered_at, 3)})
        self.history = self.history[-self.max_history:]
        return entered

    def context_history(self) -> List[Dict[str, Any]]:
        return list(self.history)

    def update_graph(self, graph: KnowledgeGraph,
                     attach_node_ids: Optional[List[str]] = None) -> int:
        """Upsert active context nodes; attach the given nodes to them."""
        touched = 0
        for name in sorted(self.active):
            context_node = graph.upsert_node(NodeType.CONTEXT, name,
                                             source_module="context_tracker")
            touched += 1
            for node_id in attach_node_ids or []:
                if node_id in graph.nodes and node_id != context_node.node_id:
                    graph.upsert_edge(node_id, EdgeType.BELONGS_TO_CONTEXT,
                                      context_node, weight_delta=0.2)
        return touched

    def to_dict(self) -> Dict[str, Any]:
        return {
            "active": sorted(self.active),
            "known_contexts": list(CONTEXTS),
            "history_tail": self.history[-10:],
        }
