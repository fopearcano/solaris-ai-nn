"""CausalAssociationModel -- candidates, never proven causes.

Evidence streams: temporal precedence (A happened before B, repeatedly),
co-occurrence, reaction feedback (B carried valence after A), embodied
intervention (the system's own action preceded the change -- the closest
thing to an experiment it has), and counterfactual replay divergence
(simulated; weighted down and always marked). The output label is
``causes_candidate`` with confidence and evidence counts attached --
the model never says "causes".
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .edges import EdgeType
from .graph import KnowledgeGraph
from .nodes import NodeType

# How much each evidence kind contributes to a candidate's score.
EVIDENCE_WEIGHTS = {
    "precedence": 1.0,
    "co_occurrence": 0.5,
    "feedback": 1.5,
    "intervention": 2.0,       # the system's own action preceded the effect
    "counterfactual": 0.5,     # simulated; never dominates real evidence
}


@dataclass
class CausalCandidate:
    source: str
    target: str
    evidence: Dict[str, int] = field(default_factory=lambda: {
        k: 0 for k in EVIDENCE_WEIGHTS})
    simulated_evidence: int = 0
    first_seen_at: float = field(default_factory=time.time)
    last_seen_at: float = field(default_factory=time.time)

    def score(self) -> float:
        raw = sum(EVIDENCE_WEIGHTS[k] * n for k, n in self.evidence.items())
        return round(raw, 4)

    def confidence(self) -> float:
        total = sum(self.evidence.values())
        return round(min(0.9, total / (total + 3.0)), 4)  # capped below 0.95

    def evidence_count(self) -> int:
        return sum(self.evidence.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source, "target": self.target,
            "label": "causes_candidate",  # structurally hedged
            "score": self.score(), "confidence": self.confidence(),
            "evidence": dict(self.evidence),
            "evidence_count": self.evidence_count(),
            "simulated_evidence": self.simulated_evidence,
        }


@dataclass
class CausalAssociationModel:
    """Scores candidate causal relations from multiple evidence streams."""

    candidates: Dict[Tuple[str, str], CausalCandidate] = field(
        default_factory=dict)

    def _candidate(self, source: str, target: str) -> CausalCandidate:
        key = (str(source), str(target))
        candidate = self.candidates.get(key)
        if candidate is None:
            candidate = CausalCandidate(source=key[0], target=key[1])
            self.candidates[key] = candidate
        return candidate

    def observe_chain(self, events: List[Dict[str, Any]]) -> int:
        """Consecutive labelled events become precedence/feedback evidence.

        Each event dict: ``label`` (required), optional ``valence``,
        ``intervention`` (the system acted), ``simulated`` (offline replay).
        """
        observed = 0
        for first, second in zip(events, events[1:]):
            source = first.get("label")
            target = second.get("label")
            if not source or not target or source == target:
                continue
            candidate = self._candidate(source, target)
            simulated = bool(first.get("simulated")
                             or second.get("simulated"))
            kind = "precedence"
            if first.get("intervention"):
                kind = "intervention"
            elif second.get("valence") is not None:
                kind = "feedback"
            if simulated:
                kind = "counterfactual"
                candidate.simulated_evidence += 1
            candidate.evidence[kind] += 1
            candidate.last_seen_at = time.time()
            observed += 1
        return observed

    def observe_co_occurrence(self, a: str, b: str) -> None:
        self._candidate(a, b).evidence["co_occurrence"] += 1

    def observe_counterfactual_divergence(self, source: str, target: str,
                                          divergence: float) -> None:
        """Counterfactual replay: divergence supports the candidate (marked)."""
        candidate = self._candidate(source, target)
        if divergence >= 0.3:
            candidate.evidence["counterfactual"] += 1
        candidate.simulated_evidence += 1

    # -- readings ---------------------------------------------------------------

    def score_candidate(self, source: str, target: str) -> Dict[str, Any]:
        candidate = self.candidates.get((str(source), str(target)))
        if candidate is None:
            return {"source": source, "target": target, "score": 0.0,
                    "confidence": 0.0, "evidence_count": 0,
                    "note": "no evidence observed for this pair"}
        return candidate.to_dict()

    def top_candidates(self, limit: int = 20) -> List[Dict[str, Any]]:
        ranked = sorted(self.candidates.values(),
                        key=lambda c: (-c.score(), c.source, c.target))
        return [c.to_dict() for c in ranked[:limit]]

    def explain_candidate(self, source: str, target: str) -> str:
        data = self.score_candidate(source, target)
        if data["evidence_count"] == 0 and not data.get("simulated_evidence"):
            return (f"No evidence links {source!r} to {target!r}; the model "
                    "does not know whether they are related.")
        parts = [f"{n}x {kind}" for kind, n in data["evidence"].items()
                 if n > 0]
        simulated_note = ""
        if data["simulated_evidence"]:
            simulated_note = (f" ({data['simulated_evidence']} of the "
                              "observations came from offline simulated "
                              "replay)")
        return (f"{source!r} -> {target!r} is a candidate causal relation "
                f"(confidence {data['confidence']}), based on: "
                f"{', '.join(parts)}{simulated_note}. This is an observed "
                "association, not proven causation.")

    def update_graph(self, graph: KnowledgeGraph, limit: int = 50) -> int:
        touched = 0
        for data in self.top_candidates(limit):
            if data["score"] <= 0:
                continue
            source = graph.upsert_node(NodeType.STATE, data["source"],
                                       source_module="causal_model")
            target = graph.upsert_node(NodeType.STATE, data["target"],
                                       source_module="causal_model")
            edge = graph.upsert_edge(
                source, EdgeType.CAUSES_CANDIDATE, target, weight_delta=0.0,
                evidence={"evidence": data["evidence"],
                          "simulated_evidence": data["simulated_evidence"]})
            edge.weight = data["score"]
            edge.confidence = data["confidence"]
            edge.observation_count = data["evidence_count"]
            edge.offline_observation_count = data["simulated_evidence"]
            touched += 1
        return touched

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_count": len(self.candidates),
            "top_candidates": self.top_candidates(5),
            "note": "labels are causes_candidate; confidence is capped and "
                    "evidence counts are exposed; nothing is proven",
        }
