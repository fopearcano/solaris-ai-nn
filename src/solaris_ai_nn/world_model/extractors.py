"""Extractors -- runtime data becomes graph observations, nothing more.

Each extractor reads what an existing layer already records (signals, the
GridWorld, meaning atoms, latent reports, pilot stream events) and upserts
nodes/edges. Nothing is invented: if a source cannot be read, the extractor
records an ``unknown`` node with the reason. Offline/counterfactual evidence
is always passed through with ``offline=True``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .edges import EdgeType
from .graph import KnowledgeGraph
from .nodes import NodeType
from .safety import WorldModelSafety


def _payload_category(payload: Any) -> str:
    """A bounded, readable category label for a payload."""
    if payload in (None, "None", ""):
        return "(none)"
    text = str(payload)
    return text[:40]


@dataclass
class _BaseExtractor:
    safety: WorldModelSafety = field(default_factory=WorldModelSafety)
    extracted: int = field(default=0, init=False)
    unknowns: int = field(default=0, init=False)

    def _safe_node(self, graph: KnowledgeGraph, node_type: str, label: str,
                   source_module: str, **metadata: Any):
        """Upsert with the safety gate; unsafe labels become unknown nodes."""
        report = self.safety.validate_node(node_type, label)
        if not report.safe:
            self.unknowns += 1
            return graph.upsert_node(
                NodeType.UNKNOWN, f"rejected:{_payload_category(label)}",
                source_module=source_module,
                reason=report.violations[0][:120])
        self.extracted += 1
        return graph.upsert_node(node_type, label,
                                 source_module=source_module, **metadata)

    def snapshot(self) -> Dict[str, Any]:
        return {"extractor": type(self).__name__,
                "extracted": self.extracted, "unknowns": self.unknowns}


@dataclass
class SignalGraphExtractor(_BaseExtractor):
    """Canonical signals -> signal_type / stimulus_pattern structure."""

    def extract(self, graph: KnowledgeGraph, signal: Any,
                result: Optional[Dict[str, Any]] = None,
                context_label: Optional[str] = None) -> List[str]:
        kind = getattr(signal, "kind", None) or (
            result or {}).get("input_type") or "UnknownSignal"
        type_node = self._safe_node(graph, NodeType.SIGNAL_TYPE, kind,
                                    "signal_extractor")
        touched = [type_node.node_id]

        payload = getattr(signal, "payload", None)
        category = _payload_category(payload)
        is_absence = bool(getattr(signal, "is_absence", False)
                          or (result or {}).get("is_absence"))
        if is_absence:
            pattern = self._safe_node(graph, NodeType.STIMULUS_PATTERN,
                                      "absence", "signal_extractor")
        else:
            pattern = self._safe_node(graph, NodeType.STIMULUS_PATTERN,
                                      category, "signal_extractor")
        graph.upsert_edge(type_node, EdgeType.CO_OCCURS_WITH, pattern,
                          evidence={"kind": kind, "payload": category})
        touched.append(pattern.node_id)

        # Stimulus -> suggested action (Push -> Desire -> Action collapses to
        # the bridge's suggestion when a result dict is available).
        if result is not None and result.get("suggested_action"):
            action = self._safe_node(graph, NodeType.ACTION,
                                     result["suggested_action"],
                                     "signal_extractor")
            graph.upsert_edge(pattern, EdgeType.PRODUCES, action,
                              weight_delta=float(
                                  result.get("confidence", 0.5) or 0.5),
                              evidence={"step": result.get("step")})
            touched.append(action.node_id)

        if context_label:
            context = self._safe_node(graph, NodeType.CONTEXT, context_label,
                                      "signal_extractor")
            graph.upsert_edge(pattern, EdgeType.BELONGS_TO_CONTEXT, context)
            touched.append(context.node_id)
        return touched

    def extract_reaction(self, graph: KnowledgeGraph, action_label: str,
                         valence: float) -> List[str]:
        action = self._safe_node(graph, NodeType.ACTION, action_label,
                                 "signal_extractor")
        bucket = ("positive" if valence > 0.15
                  else "negative" if valence < -0.15 else "neutral")
        reaction = self._safe_node(graph, NodeType.REACTION,
                                   f"valence_{bucket}", "signal_extractor")
        edge_type = (EdgeType.REINFORCES if valence > 0
                     else EdgeType.INHIBITS if valence < 0
                     else EdgeType.CO_OCCURS_WITH)
        graph.upsert_edge(action, EdgeType.PRODUCES, reaction,
                          weight_delta=abs(float(valence)) or 0.1,
                          evidence={"valence": round(float(valence), 3)})
        graph.upsert_edge(reaction, edge_type, action,
                          weight_delta=abs(float(valence)) or 0.1)
        return [action.node_id, reaction.node_id]


@dataclass
class EmbodimentGraphExtractor(_BaseExtractor):
    """GridWorld experience -> objects, places, boundaries, outcomes."""

    def extract_world(self, graph: KnowledgeGraph, world: Any) -> List[str]:
        touched: List[str] = []
        place = self._safe_node(
            graph, NodeType.PLACE,
            f"grid_{world.width}x{world.height}", "embodiment_extractor")
        touched.append(place.node_id)
        for (x, y), kind in sorted(getattr(world, "objects", {}).items()):
            obj = self._safe_node(graph, NodeType.OBJECT, kind,
                                  "embodiment_extractor")
            graph.upsert_edge(obj, EdgeType.INSIDE, place,
                              evidence={"position": [x, y]})
            touched.append(obj.node_id)
        boundary = self._safe_node(graph, NodeType.BOUNDARY, "grid_edge",
                                   "embodiment_extractor")
        graph.upsert_edge(boundary, EdgeType.SELF_BOUNDARY, place)
        touched.append(boundary.node_id)
        return touched

    def extract_action_result(self, graph: KnowledgeGraph,
                              result: Any) -> List[str]:
        data = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        action = self._safe_node(graph, NodeType.ACTION,
                                 data.get("action", "unknown_action"),
                                 "embodiment_extractor")
        touched = [action.node_id]
        blocked = data.get("blocked_reason")
        if blocked:
            blocker_type = (NodeType.OBJECT if blocked in
                            ("obstacle", "wall") else NodeType.BOUNDARY)
            blocker = self._safe_node(graph, blocker_type, blocked,
                                      "embodiment_extractor")
            graph.upsert_edge(action, EdgeType.BLOCKED_BY, blocker,
                              evidence={"consequence":
                                        data.get("consequence")})
            touched.append(blocker.node_id)
        elif data.get("executed"):
            outcome = self._safe_node(
                graph, NodeType.STATE,
                _payload_category(data.get("consequence") or "moved"),
                "embodiment_extractor")
            graph.upsert_edge(action, EdgeType.PRODUCES, outcome,
                              evidence={"events": data.get("events")})
            touched.append(outcome.node_id)
        return touched

    def extract_reaction(self, graph: KnowledgeGraph, action_label: str,
                         valence: float, marker: Optional[str] = None,
                         ) -> List[str]:
        touched = SignalGraphExtractor(safety=self.safety).extract_reaction(
            graph, action_label, valence)
        if marker:  # reward_marker -> positive, danger_marker -> negative
            obj = self._safe_node(graph, NodeType.OBJECT, marker,
                                  "embodiment_extractor")
            bucket = "positive" if valence > 0 else "negative"
            reaction = graph.get_node(NodeType.REACTION, f"valence_{bucket}")
            if reaction is not None:
                graph.upsert_edge(obj, EdgeType.PRODUCES, reaction,
                                  weight_delta=abs(float(valence)) or 0.1)
                touched.append(obj.node_id)
        return touched


@dataclass
class LanguageGraphExtractor(_BaseExtractor):
    """Meaning atoms and causal links -> graph structure, confidence kept."""

    _CATEGORY_TO_TYPE = {
        "signal": NodeType.SIGNAL_TYPE, "substrate": NodeType.STATE,
        "readout": NodeType.STATE, "habit": NodeType.HABIT,
        "memory": NodeType.STATE, "embodiment": NodeType.OBJECT,
        "inner_map": NodeType.SELF_REFERENCE,
        "continuity": NodeType.SELF_REFERENCE, "safety": NodeType.BOUNDARY,
    }

    def extract_atoms(self, graph: KnowledgeGraph,
                      atoms: List[Any]) -> List[str]:
        touched: List[str] = []
        for atom in atoms:
            data = atom.to_dict() if hasattr(atom, "to_dict") else dict(atom)
            node_type = self._CATEGORY_TO_TYPE.get(
                str(data.get("category", "unknown")), NodeType.UNKNOWN)
            node = self._safe_node(graph, node_type,
                                   data.get("subject", "unlabelled"),
                                   "language_extractor",
                                   predicate=data.get("predicate"))
            node.metadata["last_value"] = str(data.get("value"))[:80]
            touched.append(node.node_id)
        return touched

    def extract_causal_trace(self, graph: KnowledgeGraph,
                             trace: Any) -> List[str]:
        data = trace.to_dict() if hasattr(trace, "to_dict") else dict(trace)
        touched: List[str] = []
        for link in data.get("links", []):
            source = self._safe_node(graph, NodeType.STATE,
                                     link.get("source", "unlabelled"),
                                     "language_extractor")
            target = self._safe_node(graph, NodeType.STATE,
                                     link.get("target", "unlabelled"),
                                     "language_extractor")
            confidence = float(link.get("confidence", 0.5) or 0.5)
            edge_type = (EdgeType.CAUSES_CANDIDATE if confidence >= 0.5
                         else EdgeType.CO_OCCURS_WITH)
            edge = graph.upsert_edge(source, edge_type, target,
                                     weight_delta=confidence,
                                     evidence={"relation":
                                               link.get("relation")})
            # Preserve the language layer's confidence honestly: the edge
            # never reports more confidence than its weakest source.
            edge.metadata["language_confidence"] = confidence
            touched.extend([source.node_id, target.node_id])
        return touched


@dataclass
class LatentGraphExtractor(_BaseExtractor):
    """Latent replay/counterfactual/Mysterium evidence -> offline structure."""

    def extract_latent_summary(self, graph: KnowledgeGraph,
                               summary: Dict[str, Any]) -> List[str]:
        touched: List[str] = []
        for reason in summary.get("mysterium_reasons", []) or []:
            unknown = self._safe_node(graph, NodeType.UNKNOWN,
                                      _payload_category(reason),
                                      "latent_extractor")
            unknown.metadata["mysterium"] = True
            touched.append(unknown.node_id)
        mode = summary.get("mode")
        if mode:
            context = self._safe_node(graph, NodeType.CONTEXT, str(mode),
                                      "latent_extractor")
            touched.append(context.node_id)
        return touched

    def extract_dream_traces(self, graph: KnowledgeGraph,
                             dreams: List[Dict[str, Any]]) -> List[str]:
        touched: List[str] = []
        for dream in dreams:
            schema = self._safe_node(
                graph, NodeType.LATENT_SCHEMA,
                f"counterfactual_{dream.get('counterfactual_kind', '?')}",
                "latent_extractor", offline=True)
            divergence = (dream.get("divergence") or {}).get("score", 0.0)
            unknown_target = self._safe_node(graph, NodeType.UNKNOWN,
                                             "counterfactual_divergence",
                                             "latent_extractor")
            graph.upsert_edge(
                schema, EdgeType.UNKNOWN_RELATION, unknown_target,
                weight_delta=float(divergence or 0.0) or 0.1,
                evidence={"dream_id": dream.get("dream_id"),
                          "offline": True, "simulated": True},
                offline=True)  # offline evidence, counted separately
            touched.append(schema.node_id)
        return touched

    def extract_schemas(self, graph: KnowledgeGraph,
                        schemas: List[Any]) -> List[str]:
        touched: List[str] = []
        for schema in schemas:
            data = (schema.to_dict() if hasattr(schema, "to_dict")
                    else dict(schema))
            node = self._safe_node(graph, NodeType.LATENT_SCHEMA,
                                   data.get("pattern", "unlabelled"),
                                   "latent_extractor",
                                   support=data.get("support_count"))
            action_label = data.get("dominant_action")
            if action_label:
                action = self._safe_node(graph, NodeType.ACTION,
                                         action_label, "latent_extractor")
                graph.upsert_edge(node, EdgeType.PREDICTS, action,
                                  weight_delta=float(
                                      data.get("support_count", 1) or 1))
                touched.append(action.node_id)
            touched.append(node.node_id)
        return touched

    def extract_anticipation(self, graph: KnowledgeGraph,
                             snapshot: Dict[str, Any]) -> List[str]:
        node = self._safe_node(graph, NodeType.SELF_REFERENCE,
                               "anticipation_tracker", "latent_extractor",
                               rolling_accuracy=snapshot.get(
                                   "rolling_accuracy"),
                               miss_streak=snapshot.get("miss_streak"))
        return [node.node_id]


@dataclass
class PilotStreamGraphExtractor(_BaseExtractor):
    """Validated read-only stream events -> source/modality/pattern nodes."""

    def extract_event(self, graph: KnowledgeGraph,
                      event: Dict[str, Any]) -> List[str]:
        from ..pilot.data_contracts import validate_jsonl_event

        check = validate_jsonl_event(dict(event))
        if not check.valid:
            # Already blocked upstream by pilot safety; keep an audit-only
            # unknown node, never an entity/action.
            self.unknowns += 1
            node = graph.upsert_node(
                NodeType.UNKNOWN, "rejected_stream_payload",
                source_module="pilot_extractor",
                reason=check.reasons[0][:120])
            return [node.node_id]
        normalized = check.normalized
        source = self._safe_node(graph, NodeType.ENTITY,
                                 normalized["source"], "pilot_extractor")
        modality = self._safe_node(graph, NodeType.SIGNAL_TYPE,
                                   f"modality_{normalized['modality']}",
                                   "pilot_extractor")
        pattern = self._safe_node(graph, NodeType.STIMULUS_PATTERN,
                                  _payload_category(normalized["payload"]),
                                  "pilot_extractor")
        graph.upsert_edge(source, EdgeType.PRODUCES, pattern,
                          evidence={"modality": normalized["modality"]})
        graph.upsert_edge(pattern, EdgeType.CO_OCCURS_WITH, modality)
        context = self._safe_node(graph, NodeType.CONTEXT, "pilot_stream",
                                  "pilot_extractor")
        graph.upsert_edge(pattern, EdgeType.BELONGS_TO_CONTEXT, context)
        return [source.node_id, modality.node_id, pattern.node_id]
