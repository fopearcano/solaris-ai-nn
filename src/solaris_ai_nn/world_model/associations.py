"""AssociationLearner -- counted, decaying pairwise associations.

The learner watches repeated pairings (pattern->action, action->valence,
context->signal, entity->outcome, absence->tendency, fracture->tendency,
energy->rest, boundary->blocked action) and keeps simple count/weight
statistics. No deep learning: the entire model is a dictionary you can
print.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .edges import EdgeType
from .graph import KnowledgeGraph
from .nodes import NodeType

# kind -> (source node type, target node type, edge type)
ASSOCIATION_KINDS: Dict[str, Tuple[str, str, str]] = {
    "pattern_action": (NodeType.STIMULUS_PATTERN, NodeType.ACTION,
                       EdgeType.PRODUCES),
    "action_valence": (NodeType.ACTION, NodeType.REACTION,
                       EdgeType.PRODUCES),
    "context_signal": (NodeType.CONTEXT, NodeType.SIGNAL_TYPE,
                       EdgeType.PREDICTS),
    "entity_outcome": (NodeType.ENTITY, NodeType.STATE, EdgeType.PRODUCES),
    "absence_action": (NodeType.STIMULUS_PATTERN, NodeType.ACTION,
                       EdgeType.PRODUCES),
    "fracture_tendency": (NodeType.STATE, NodeType.STATE,
                          EdgeType.CO_OCCURS_WITH),
    "energy_rest": (NodeType.STATE, NodeType.ACTION, EdgeType.PRODUCES),
    "boundary_blocked": (NodeType.ACTION, NodeType.BOUNDARY,
                         EdgeType.BLOCKED_BY),
}


@dataclass
class Association:
    kind: str
    source: str
    target: str
    count: int = 0
    weight: float = 0.0
    last_observed_at: float = field(default_factory=time.time)

    def key(self) -> Tuple[str, str, str]:
        return (self.kind, self.source, self.target)

    def confidence(self) -> float:
        return round(min(0.95, self.count / (self.count + 2.0)), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {**self.__dict__, "confidence": self.confidence()}


@dataclass
class AssociationLearner:
    """Counts and decays pairwise associations; writes them into the graph."""

    decay_factor: float = 0.995
    associations: Dict[Tuple[str, str, str], Association] = field(
        default_factory=dict)
    observed_total: int = field(default=0, init=False)

    def observe(self, event: Dict[str, Any]) -> List[Association]:
        """One observation; the event names what was paired with what.

        Recognized keys (any subset): pattern+action, action+valence,
        context+signal, entity+outcome, is_absence+action,
        logos_fracture(+tendency), energy_low(+action), blocked_reason+action.
        """
        out: List[Association] = []

        def hit(kind: str, source: Any, target: Any,
                weight: float = 1.0) -> None:
            if source is None or target is None:
                return
            key = (kind, str(source), str(target))
            assoc = self.associations.get(key)
            if assoc is None:
                assoc = Association(kind=kind, source=str(source),
                                    target=str(target))
                self.associations[key] = assoc
            assoc.count += 1
            assoc.weight += weight
            assoc.last_observed_at = time.time()
            self.observed_total += 1
            out.append(assoc)

        pattern = event.get("pattern")
        action = event.get("action")
        if event.get("is_absence"):
            hit("absence_action", "absence", action)
        elif pattern is not None:
            hit("pattern_action", pattern, action)
        valence = event.get("valence")
        if valence is not None and action is not None:
            bucket = ("valence_positive" if valence > 0.15 else
                      "valence_negative" if valence < -0.15
                      else "valence_neutral")
            hit("action_valence", action, bucket, abs(float(valence)) or 0.1)
        if event.get("context") is not None and event.get("signal") is not None:
            hit("context_signal", event["context"], event["signal"])
        if event.get("entity") is not None and event.get("outcome") is not None:
            hit("entity_outcome", event["entity"], event["outcome"])
        fracture = event.get("logos_fracture")
        if fracture is not None and float(fracture) >= 0.5:
            hit("fracture_tendency", "high_logos_fracture",
                event.get("tendency", "exploration"))
        if event.get("energy_low"):
            hit("energy_rest", "low_energy", event.get("rest_action", "rest"))
        if event.get("blocked_reason") and action is not None:
            hit("boundary_blocked", action, event["blocked_reason"])
        return out

    def decay(self) -> None:
        for assoc in self.associations.values():
            assoc.weight = round(assoc.weight * self.decay_factor, 6)

    # -- graph + readings ---------------------------------------------------------

    def update_graph(self, graph: KnowledgeGraph) -> int:
        """Write the learned associations into the graph; returns edges touched."""
        touched = 0
        for assoc in sorted(self.associations.values(),
                            key=lambda a: a.key()):
            source_type, target_type, edge_type = ASSOCIATION_KINDS[assoc.kind]
            source = graph.upsert_node(source_type, assoc.source,
                                       source_module="association_learner")
            target = graph.upsert_node(target_type, assoc.target,
                                       source_module="association_learner")
            edge = graph.upsert_edge(
                source, edge_type, target,
                weight_delta=0.0,  # the weight is set, not accumulated again
                evidence={"association_kind": assoc.kind,
                          "count": assoc.count})
            edge.weight = round(assoc.weight, 6)
            edge.observation_count = assoc.count
            edge.confidence = assoc.confidence()
            touched += 1
        return touched

    def strongest_associations(self, limit: int = 10) -> List[Dict[str, Any]]:
        ranked = sorted(self.associations.values(),
                        key=lambda a: (-a.weight, a.key()))
        return [a.to_dict() for a in ranked[:limit]]

    def association_entropy(self) -> float:
        """Shannon entropy (bits) over the association weight distribution."""
        weights = [a.weight for a in self.associations.values()
                   if a.weight > 0]
        total = sum(weights)
        if not weights or total <= 0:
            return 0.0
        return round(-sum((w / total) * math.log2(w / total)
                          for w in weights), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "association_count": len(self.associations),
            "observed_total": self.observed_total,
            "entropy_bits": self.association_entropy(),
            "strongest": self.strongest_associations(5),
        }
