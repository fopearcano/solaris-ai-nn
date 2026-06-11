"""WorldModelBuilder -- one object that grows the graph from everything.

Owns the KnowledgeGraph plus the extractors, association learner, causal
model, context tracker, predictor, pruner, and safety gate, and exposes
``update_from_*`` entry points for each existing layer. Build statistics are
tracked so a report can say exactly where the structure came from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .associations import AssociationLearner
from .causal_model import CausalAssociationModel
from .context import ContextTracker
from .extractors import (
    EmbodimentGraphExtractor,
    LanguageGraphExtractor,
    LatentGraphExtractor,
    PilotStreamGraphExtractor,
    SignalGraphExtractor,
)
from .graph import KnowledgeGraph
from .nodes import NodeType
from .prediction import WorldModelPredictor
from .pruning import GraphSynthesisPruner
from .safety import WorldModelSafety


@dataclass
class WorldModelBuilder:
    """Grows and accounts for the world model."""

    graph: KnowledgeGraph = field(default_factory=KnowledgeGraph)
    safety: WorldModelSafety = field(default_factory=WorldModelSafety)
    anticipation: Any = None  # optional latent.AnticipationTracker
    mysterium: Any = None     # optional latent.MysteriumTracker

    def __post_init__(self) -> None:
        self.signal_extractor = SignalGraphExtractor(safety=self.safety)
        self.embodiment_extractor = EmbodimentGraphExtractor(
            safety=self.safety)
        self.language_extractor = LanguageGraphExtractor(safety=self.safety)
        self.latent_extractor = LatentGraphExtractor(safety=self.safety)
        self.pilot_extractor = PilotStreamGraphExtractor(safety=self.safety)
        self.associations = AssociationLearner()
        self.causal = CausalAssociationModel()
        self.context = ContextTracker()
        self.predictor = WorldModelPredictor(anticipation=self.anticipation,
                                             mysterium=self.mysterium)
        self.pruner = GraphSynthesisPruner(safety=self.safety)
        self.stats: Dict[str, int] = {
            "signal_updates": 0, "trace_updates": 0, "meaning_updates": 0,
            "embodiment_updates": 0, "latent_updates": 0, "pilot_updates": 0,
            "sidecar_updates": 0,
        }
        self._self_node()

    def _self_node(self) -> None:
        self.graph.upsert_node(
            NodeType.SELF_REFERENCE, "solaris_ai_nn",
            source_module="builder",
            note="the system's own node; observations, not identity claims")

    # -- update entry points -------------------------------------------------------

    def update_from_signal(self, signal: Any,
                           result: Optional[Dict[str, Any]] = None,
                           context: Optional[Dict[str, Any]] = None) -> List[str]:
        """One processed signal (and the bridge's result dict, if any)."""
        contexts = self.context.current_context(context or {})
        self.context.observe_context_change(contexts)
        touched = self.signal_extractor.extract(
            self.graph, signal, result=result, context_label=contexts[0])
        self.context.update_graph(self.graph, attach_node_ids=touched[:2])
        if result is not None:
            self.associations.observe({
                "pattern": result.get("pattern_key"),
                "action": result.get("suggested_action"),
                "is_absence": result.get("is_absence"),
                "logos_fracture": result.get("logos_fracture"),
                "context": contexts[0],
                "signal": result.get("input_type"),
            })
        self.stats["signal_updates"] += 1
        return touched

    def update_from_reaction(self, action_label: str,
                             valence: float) -> List[str]:
        touched = self.signal_extractor.extract_reaction(
            self.graph, action_label, valence)
        self.associations.observe({"action": action_label,
                                   "valence": valence})
        return touched

    def update_from_trace(self, trace: Any, window: int = 100) -> int:
        """Recent trace records become precedence chains + associations."""
        records = (trace.recent(window) if hasattr(trace, "recent")
                   else list(trace)[-window:])
        chain: List[Dict[str, Any]] = []
        last_action: Optional[str] = None
        for record in records:
            row = record.to_row() if hasattr(record, "to_row") else dict(record)
            category = row.get("category")
            if category == "event":
                label = (f"signal:{row.get('kind', '?')}"
                         if not row.get("is_absence") else "signal:absence")
                chain.append({"label": label})
            elif category == "action":
                last_action = row.get("action")
                chain.append({"label": f"action:{last_action}",
                              "intervention": True})
            elif category == "reaction":
                chain.append({"label": "reaction",
                              "valence": row.get("valence")})
                if last_action is not None:
                    self.associations.observe({
                        "action": last_action,
                        "valence": row.get("valence")})
                    self.update_from_reaction(last_action,
                                              float(row.get("valence", 0.0)
                                                    or 0.0))
        observed = self.causal.observe_chain(chain)
        self.causal.update_graph(self.graph)
        self.associations.update_graph(self.graph)
        self.stats["trace_updates"] += 1
        return observed

    def update_from_meaning_trace(self, meaning_trace: Any) -> List[str]:
        """MeaningAtoms (or a MeaningTraceBuilder) become graph structure."""
        atoms = getattr(meaning_trace, "atoms", meaning_trace) or []
        touched = self.language_extractor.extract_atoms(self.graph,
                                                        list(atoms)[-200:])
        self.stats["meaning_updates"] += 1
        return touched

    def update_from_causal_trace(self, causal_trace: Any) -> List[str]:
        touched = self.language_extractor.extract_causal_trace(self.graph,
                                                               causal_trace)
        self.stats["meaning_updates"] += 1
        return touched

    def update_from_embodiment(self, runner_or_result: Any) -> List[str]:
        """A SensorimotorSimulationRunner (or one ActionResult)."""
        touched: List[str] = []
        world = getattr(runner_or_result, "world", None)
        if world is not None:
            touched += self.embodiment_extractor.extract_world(self.graph,
                                                               world)
            for result in list(getattr(runner_or_result, "action_history",
                                       []))[-50:]:
                touched += self.embodiment_extractor.extract_action_result(
                    self.graph, result)
                self.associations.observe({
                    "action": result.action,
                    "blocked_reason": result.blocked_reason})
            valences = list(getattr(runner_or_result, "reaction_valences",
                                    []))[-50:]
            actions = list(getattr(runner_or_result, "action_history",
                                   []))[-50:]
            for result, valence in zip(actions, valences):
                touched += self.embodiment_extractor.extract_reaction(
                    self.graph, result.action, valence)
            body = getattr(runner_or_result, "body", None)
            if body is not None and getattr(body.energy, "is_low", False):
                self.associations.observe({"energy_low": True})
        else:  # a single ActionResult
            touched += self.embodiment_extractor.extract_action_result(
                self.graph, runner_or_result)
        self.context.observe_context_change(["embodied_gridworld"])
        self.context.update_graph(self.graph, attach_node_ids=touched[:3])
        self.stats["embodiment_updates"] += 1
        return touched

    def update_from_latent_report(self, report_or_summary: Any,
                                  dreams: Optional[List[Dict[str, Any]]]
                                  = None,
                                  schemas: Optional[List[Any]] = None,
                                  ) -> List[str]:
        """Latent evidence (always marked offline where simulated)."""
        summary = (report_or_summary if isinstance(report_or_summary, dict)
                   else getattr(report_or_summary, "sections", {}) or {})
        touched = self.latent_extractor.extract_latent_summary(self.graph,
                                                               summary)
        if dreams:
            touched += self.latent_extractor.extract_dream_traces(self.graph,
                                                                  dreams)
        if schemas:
            touched += self.latent_extractor.extract_schemas(self.graph,
                                                             schemas)
        self.stats["latent_updates"] += 1
        return touched

    def update_from_pilot_event(self, event: Dict[str, Any]) -> List[str]:
        touched = self.pilot_extractor.extract_event(self.graph, event)
        self.stats["pilot_updates"] += 1
        return touched

    def update_from_sidecar_mirror(self, mirror: Any,
                                   limit: int = 100) -> List[str]:
        """Mirrored Solaris signals (observed, never created by us).

        Sidecar *suggestions* become suggestion-labelled latent_schema
        nodes -- explicitly not committed action nodes.
        """
        touched: List[str] = []
        rows = list(getattr(mirror, "rows", None)
                    or getattr(mirror, "signals", None) or mirror or [])
        for row in rows[-limit:]:
            data = row if isinstance(row, dict) else {
                "kind": getattr(row, "kind", type(row).__name__),
                "payload": getattr(row, "payload", None)}
            kind = str(data.get("kind", data.get("signal_type", "Signal")))
            node = self.graph.upsert_node(NodeType.SIGNAL_TYPE,
                                          f"solaris_{kind}",
                                          source_module="sidecar")
            touched.append(node.node_id)
            if "suggestion" in kind.lower() or data.get("suggestion"):
                suggestion = self.graph.upsert_node(
                    NodeType.LATENT_SCHEMA,
                    f"suggestion_{data.get('payload', 'unlabelled')}",
                    source_module="sidecar",
                    committed=False, note="suggestion only, never an Action")
                touched.append(suggestion.node_id)
        self.context.observe_context_change(["solaris_sidecar"])
        self.context.update_graph(self.graph, attach_node_ids=touched[:3])
        self.stats["sidecar_updates"] += 1
        return touched

    # -- readings -------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "node_counts_by_type": self.graph.node_counts_by_type(),
            "edge_counts_by_type": self.graph.edge_counts_by_type(),
            "evidence_ratio": self.graph.evidence_ratio(),
            "stats": dict(self.stats),
            "associations": self.associations.to_dict(),
            "causal": self.causal.to_dict(),
            "context": self.context.to_dict(),
            "predictor": self.predictor.snapshot(),
            "pruner": self.pruner.snapshot(),
            "safety": self.safety.snapshot(),
        }

    def world_model_summary(self) -> Dict[str, Any]:
        """Compact world-model status for the Inner MAP."""
        strongest = self.associations.strongest_associations(1)
        top_causal = self.causal.top_candidates(1)
        unknowns = self.graph.find(node_type=NodeType.UNKNOWN)
        high_mysterium = [n.label for n in unknowns
                          if n.metadata.get("mysterium")][:5]
        return {
            "enabled": True,
            "graph_node_count": len(self.graph.nodes),
            "graph_edge_count": len(self.graph.edges),
            "strongest_association": (strongest[0] if strongest else None),
            "top_causal_candidate": (top_causal[0] if top_causal else None),
            "unknown_node_count": len(unknowns),
            "high_mysterium_areas": high_mysterium,
            "context_state": sorted(self.context.active),
            "prediction_accuracy": self.predictor.accuracy(),
            "last_pruning_proposal": (self.pruner.last_report or {}).get(
                "proposal_id"),
            "evidence_ratio": self.graph.evidence_ratio(),
            "world_model_report_path": None,  # set by callers that save one
        }

    def to_report(self):
        from .reports import WorldModelReportBuilder

        return WorldModelReportBuilder(builder=self).build()
