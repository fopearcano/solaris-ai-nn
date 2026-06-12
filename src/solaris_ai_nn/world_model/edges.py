"""Graph edges -- observed relations, never proven facts.

Every edge carries its weight, confidence, observation count, and bounded
evidence references. Causal language is structurally hedged: the strongest
causal label available is ``causes_candidate``. Offline/simulated evidence
(dream/counterfactual replay) is counted separately and never inflates the
real observation count.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .nodes import confidence_from_count

MAX_EVIDENCE_REFS = 20


class EdgeType:
    CO_OCCURS_WITH = "co_occurs_with"
    PRECEDES = "precedes"
    CAUSES_CANDIDATE = "causes_candidate"
    REINFORCES = "reinforces"
    INHIBITS = "inhibits"
    BELONGS_TO_CONTEXT = "belongs_to_context"
    NEAR = "near"
    INSIDE = "inside"
    BLOCKED_BY = "blocked_by"
    PRODUCES = "produces"
    PREDICTS = "predicts"
    CONTRADICTS = "contradicts"
    UNKNOWN_RELATION = "unknown_relation"
    SELF_BOUNDARY = "self_boundary"
    # Ego / self-model (Prompt 18).
    OPERATES_UNDER = "operates_under"
    HOLDS_AUTHORITY = "holds_authority"
    BOUNDED_BY = "bounded_by"
    SEPARATES_EVIDENCE = "separates_evidence"
    ATTRIBUTED_TO = "attributed_to"
    # Proto-language (Prompt 22).
    GROUNDED_IN = "grounded_in"

    ALL = (CO_OCCURS_WITH, PRECEDES, CAUSES_CANDIDATE, REINFORCES, INHIBITS,
           BELONGS_TO_CONTEXT, NEAR, INSIDE, BLOCKED_BY, PRODUCES, PREDICTS,
           CONTRADICTS, UNKNOWN_RELATION, SELF_BOUNDARY, OPERATES_UNDER,
           HOLDS_AUTHORITY, BOUNDED_BY, SEPARATES_EVIDENCE, ATTRIBUTED_TO,
           GROUNDED_IN)


def edge_id_for(source_node_id: str, edge_type: str,
                target_node_id: str) -> str:
    """Deterministic edge id: one edge per (source, type, target) triple."""
    return f"{source_node_id}|{edge_type}|{target_node_id}"


@dataclass
class GraphEdge:
    """One observed relation between two nodes."""

    edge_id: str
    source_node_id: str
    target_node_id: str
    type: str
    weight: float = 0.0
    confidence: float = 0.0
    observation_count: int = 0
    offline_observation_count: int = 0
    last_observed_at: float = field(default_factory=time.time)
    evidence_refs: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in EdgeType.ALL:
            raise ValueError(f"unknown edge type {self.type!r}")

    def observe(self, weight_delta: float = 1.0,
                evidence: Any = None, offline: bool = False,
                **metadata: Any) -> "GraphEdge":
        """One more observation of this relation.

        ``offline=True`` (dream/counterfactual evidence) is recorded and
        counted separately; it nudges the weight at quarter strength and
        never increases the *real* observation count.
        """
        if offline:
            self.offline_observation_count += 1
            self.weight += 0.25 * weight_delta
        else:
            self.observation_count += 1
            self.weight += weight_delta
        self.confidence = confidence_from_count(self.observation_count)
        self.last_observed_at = time.time()
        if evidence is not None:
            self.evidence_refs.append({"evidence": evidence,
                                       "offline": offline,
                                       "timestamp": self.last_observed_at})
            self.evidence_refs = self.evidence_refs[-MAX_EVIDENCE_REFS:]
        for key, value in metadata.items():
            self.metadata[key] = value
        return self

    def decay(self, factor: float = 0.99) -> None:
        self.weight = round(self.weight * factor, 6)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GraphEdge":
        valid = set(cls.__dataclass_fields__)  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in valid})
