"""World-model queries -- fixed strings, grounded answers, cautious words.

Same philosophy as the language layer's QueryInterface: normalized string
matching to deterministic handlers, honest "does not know" fallbacks, and
hedged vocabulary throughout ("observed association", "candidate causal
relation", "prediction based on graph counts").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List

from ..language.query import normalize
from ..language.schemas import QueryResult
from .nodes import NodeType


@dataclass
class WorldModelQueryInterface:
    """Answers a fixed set of questions from a WorldModelBuilder."""

    builder: Any  # WorldModelBuilder

    def __post_init__(self) -> None:
        self._handlers: Dict[str, Callable[[], "tuple[str, float]"]] = {
            "what does the world model know": self._know,
            "what is the strongest association": self._strongest,
            "what does the graph predict next": self._predict,
            "what is still unknown": self._unknown,
            "what was pruned from the graph": self._pruned,
            "what did the system learn in gridworld": self._gridworld,
        }

    def supported_queries(self) -> List[str]:
        return sorted(self._handlers)

    def answer(self, query: str) -> QueryResult:
        handler = self._handlers.get(normalize(query))
        if handler is None:
            return QueryResult(
                query=query, answered=False, confidence=0.0,
                text=("The system does not know how to answer that query. "
                      "Supported queries: "
                      + "; ".join(self.supported_queries()) + "."))
        text, confidence = handler()
        return QueryResult(query=query, answered=confidence > 0.0,
                           text=text, confidence=confidence)

    # -- handlers ---------------------------------------------------------------

    def _know(self) -> "tuple[str, float]":
        graph = self.builder.graph
        if len(graph.nodes) <= 1:  # only the self node
            return ("The world model has not observed enough to hold any "
                    "structure yet.", 0.3)
        counts = graph.node_counts_by_type()
        parts = [f"{n} {t} node(s)" for t, n in counts.items() if n]
        return (f"The world model holds {len(graph.nodes)} nodes and "
                f"{len(graph.edges)} observed relations: "
                + ", ".join(parts)
                + ". These are observed associations extracted from "
                "recorded events, not human-like understanding.", 0.9)

    def _strongest(self) -> "tuple[str, float]":
        strongest = self.builder.associations.strongest_associations(1)
        if not strongest:
            return ("No association has been observed often enough to "
                    "rank yet.", 0.3)
        a = strongest[0]
        return (f"The strongest observed association is "
                f"{a['source']!r} -> {a['target']!r} ({a['kind']}), seen "
                f"{a['count']}x with weight {a['weight']:.2f} and "
                f"confidence {a['confidence']}.", 0.9)

    def _predict(self) -> "tuple[str, float]":
        prediction = self.builder.predictor.predict_next(
            {}, self.builder.graph)
        if prediction.next_signal_type is None \
                and prediction.likely_useful_action is None:
            return ("The graph has insufficient evidence to predict "
                    "anything yet.", 0.2)
        parts = []
        if prediction.next_signal_type:
            parts.append(f"next signal type {prediction.next_signal_type!r} "
                         f"({prediction.basis.get('next_signal_type')})")
        if prediction.likely_useful_action:
            parts.append("likely useful action "
                         f"{prediction.likely_useful_action!r}")
        return ("Prediction based on graph counts: " + "; ".join(parts)
                + ". Predictions inform internal trackers and never "
                "execute actions.", 0.7)

    def _unknown(self) -> "tuple[str, float]":
        unknowns = self.builder.graph.find(node_type=NodeType.UNKNOWN)
        if not unknowns:
            return ("No unknown nodes are currently marked; this means no "
                    "unexplained structure was flagged, not that everything "
                    "is known.", 0.6)
        labels = sorted(n.label for n in unknowns)[:8]
        return (f"{len(unknowns)} region(s) of the graph are marked unknown "
                f"or insufficient-evidence: {', '.join(labels)}.", 0.85)

    def _pruned(self) -> "tuple[str, float]":
        snap = self.builder.pruner.snapshot()
        last = snap.get("last_report")
        if last is None:
            return ("No graph pruning has been proposed or applied yet.",
                    0.6)
        key = "removed" if last.get("applied") else "would_remove"
        totals = last.get(key, {})
        verb = "removed" if last.get("applied") else \
            "proposed removing (dry-run)"
        return (f"Graph synthesis {verb} {totals.get('edges', 0)} weak "
                f"edge(s), {totals.get('nodes', 0)} weak node(s), and "
                f"{totals.get('merges', 0)} redundant merge(s); evidence "
                "summaries were preserved.", 0.85)

    def _gridworld(self) -> "tuple[str, float]":
        graph = self.builder.graph
        objects = sorted(n.label for n in graph.find(
            node_type=NodeType.OBJECT)
            if "embodiment_extractor" in n.source_modules)
        blocked = [e for e in graph.edges.values() if e.type == "blocked_by"]
        if not objects and not blocked:
            return ("The world model has no GridWorld observations yet.",
                    0.3)
        parts = []
        if objects:
            parts.append(f"observed objects: {', '.join(objects[:6])}")
        if blocked:
            worst = max(blocked, key=lambda e: e.observation_count)
            parts.append(
                f"{len(blocked)} blocked-action relation(s), most often "
                f"{graph.nodes[worst.source_node_id].label!r} blocked by "
                f"{graph.nodes[worst.target_node_id].label!r} "
                f"({worst.observation_count}x)")
        return ("In GridWorld the model recorded " + "; ".join(parts)
                + ". These are observed associations from the simulation.",
                0.85)
