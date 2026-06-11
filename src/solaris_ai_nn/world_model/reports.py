"""WorldModelReportBuilder -- the graph's written account.

Counts, strongest associations, causal candidates, unknowns, contexts,
predictions, pruning, and the mandatory limitations. Markdown is saved
through the language layer, so every report is ClaimGuard-scanned.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..language.reporting import ExperimentReportBuilder, SessionReport
from .nodes import NodeType

WORLD_MODEL_LIMITATIONS = [
    "The world model stores observed associations and candidate causal "
    "relations extracted from recorded events; it does not constitute "
    "human-like understanding of anything.",
    "Causal edges are labelled causes_candidate with capped confidence; "
    "none are proven causation.",
    "Offline/counterfactual evidence is counted separately and never "
    "treated as real observation.",
    "Predictions are derived from graph counts; they inform internal "
    "trackers and never execute actions.",
]


class WorldModelReportBuilder:
    """Assembles the report from a WorldModelBuilder."""

    def __init__(self, builder: Any) -> None:
        self.builder = builder

    def build(self) -> SessionReport:
        b = self.builder
        graph = b.graph
        unknowns = graph.find(node_type=NodeType.UNKNOWN)
        report = (
            ExperimentReportBuilder(title="World model report")
            .add_metadata(node_count=len(graph.nodes),
                          edge_count=len(graph.edges))
            .add_section("graph_summary", {
                "nodes": len(graph.nodes),
                "edges": len(graph.edges),
                "evidence_ratio": graph.evidence_ratio(),
                "build_stats": dict(b.stats),
            })
            .add_section("node_counts_by_type",
                         graph.node_counts_by_type())
            .add_section("edge_counts_by_type",
                         graph.edge_counts_by_type())
            .add_section("strongest_associations",
                         b.associations.strongest_associations(8)
                         or ["no associations observed yet"])
            .add_section("top_causal_candidates",
                         b.causal.top_candidates(8)
                         or ["no causal candidates yet"])
            .add_section("unknown_nodes", {
                "count": len(unknowns),
                "labels": sorted(n.label for n in unknowns)[:15],
            })
            .add_section("high_mysterium_areas",
                         [n.label for n in unknowns
                          if n.metadata.get("mysterium")][:10]
                         or ["none marked"])
            .add_section("context_distribution", b.context.to_dict())
            .add_section("predictions", b.predictor.snapshot())
            .add_section("pruning_subtraction", b.pruner.snapshot())
            .add_section("safety", b.safety.snapshot())
        )
        embodied = graph.find(node_type=NodeType.OBJECT)
        if embodied:
            report.add_section("embodiment_knowledge", {
                "objects": sorted(n.label for n in embodied)[:10],
                "blocked_edges": len([e for e in graph.edges.values()
                                      if e.type == "blocked_by"]),
            })
        pilot_sources = [n for n in graph.find(node_type=NodeType.ENTITY)
                         if "pilot_extractor" in n.source_modules]
        if pilot_sources:
            report.add_section("pilot_stream_knowledge", {
                "sources": sorted(n.label for n in pilot_sources)[:10]})
        sidecar_nodes = [n for n in graph.nodes.values()
                         if "sidecar" in n.source_modules]
        if sidecar_nodes:
            report.add_section("sidecar_knowledge", {
                "observed": sorted(n.label for n in sidecar_nodes)[:10],
                "note": "suggestions are suggestion nodes, never committed "
                        "Actions"})
        for limitation in WORLD_MODEL_LIMITATIONS:
            report.add_limitation(limitation)
        return report.build()

    def to_dict(self) -> Dict[str, Any]:
        return self.build().to_dict()

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_markdown(self) -> str:
        return self.build().to_markdown()

    def save(self, json_path: Union[str, Path],
             md_path: Union[str, Path]) -> Dict[str, Any]:
        """Persist via the language layer (ClaimGuard scans the Markdown)."""
        from ..language.serialization import save_report

        scan = save_report(self.build(), json_path, md_path)
        return {"json": str(json_path), "markdown": str(md_path),
                "claim_guard": scan.to_dict()}
