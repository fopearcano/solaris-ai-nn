"""World-model hygiene -- mark and weaken, never silently delete evidence.

The :class:`WorldModelHygieneManager` detects contradictory edges, isolated
stale nodes, runaway edge growth, unsupported causal claims, and stale
prediction edges. It prefers marking edges ambiguous or weakening them over
deletion, requests a hypothesis test for unresolved contradictions, and never
deletes contradiction evidence silently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .repair_actions import RepairAction, RepairActionType, make_repair


@dataclass
class WorldModelHygieneManager:
    """Detects graph degradation; marks/weakens edges, preserves evidence."""

    runaway_edge_threshold: int = 5000
    hypothesis_requests: List[str] = field(default_factory=list)
    findings: List[Dict[str, Any]] = field(default_factory=list)

    def detect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        wm = (context or {}).get("world_model") or {}
        contradictions = list(wm.get("contradiction_edges") or [])
        weak = list(wm.get("weak_edges") or [])
        stale = list(wm.get("stale_prediction_edges") or [])
        isolated = list(wm.get("isolated_nodes") or [])
        unsupported = list(wm.get("unsupported_causal_claims") or [])
        edges = int(wm.get("graph_edge_count", 0) or 0)
        result = {
            "contradiction_edges": contradictions,
            "weak_edges": weak,
            "stale_prediction_edges": stale,
            "isolated_nodes": isolated,
            "unsupported_causal_claims": unsupported,
            "runaway_edge_growth": edges > self.runaway_edge_threshold,
        }
        self.findings.append(result)
        self.findings = self.findings[-50:]
        return result

    def propose(self, context: Dict[str, Any]) -> List[RepairAction]:
        detected = self.detect(context)
        actions: List[RepairAction] = []
        for edge in detected["contradiction_edges"]:
            # Mark ambiguous (preserve evidence) and request a hypothesis test.
            actions.append(make_repair(
                RepairActionType.MARK_WORLD_EDGE_AMBIGUOUS, target_ref=str(edge),
                reason="contradictory edge; evidence preserved",
                expected_benefit="flag a contradiction without deleting "
                                 "evidence"))
            self.hypothesis_requests.append(str(edge))
        for edge in detected["weak_edges"]:
            actions.append(make_repair(
                RepairActionType.WEAKEN_CONTRADICTORY_EDGE, target_ref=str(edge),
                reason="edge decayed below support threshold",
                expected_benefit="weaken an unsupported edge"))
        for edge in detected["stale_prediction_edges"]:
            actions.append(make_repair(
                RepairActionType.MARK_WORLD_EDGE_AMBIGUOUS, target_ref=str(edge),
                reason="stale prediction edge",
                expected_benefit="flag a stale prediction edge"))
        for claim in detected["unsupported_causal_claims"]:
            actions.append(make_repair(
                RepairActionType.MARK_WORLD_EDGE_AMBIGUOUS, target_ref=str(claim),
                reason="causal claim without sufficient evidence",
                expected_benefit="downgrade an unsupported causal claim"))
            self.hypothesis_requests.append(str(claim))
        return actions

    def apply_to_graph(self, graph: Any, edge_id: str,
                       weaken: bool = False) -> bool:
        """Mark an edge ambiguous (metadata) or weaken it; never delete it."""
        if graph is None:
            return False
        edge = getattr(graph, "edges", {}).get(edge_id)
        if edge is None:
            return False
        try:
            if weaken:
                edge.decay(0.5)
            edge.metadata["ambiguous"] = True
            edge.metadata["hygiene_marked"] = True
            return True
        except Exception:
            return False

    def snapshot(self) -> Dict[str, Any]:
        return {
            "hypothesis_requests": list(self.hypothesis_requests),
            "last_finding": self.findings[-1] if self.findings else None,
        }
