"""Ecology reports -- what world did the system actually live in?

The report describes the nursery configuration, the regimes and rhythms
that were active, the distribution of events, the absence/novelty/anomaly/
scarcity/delayed/seasonal structure, and (when wired) the developmental
responses that co-occurred -- with mandatory limitations and a ClaimGuard
pass before any Markdown is written.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Union

from ..language.reporting import ExperimentReportBuilder, SessionReport

ECOLOGY_LIMITATIONS = [
    "The ecology is an artificial stimulus world, not a teacher: events "
    "carry no correct-answer labels and no human feedback.",
    "Stimuli are deterministic with the seed and bounded; absence, "
    "anomaly, and deprivation windows are controlled perturbations, not "
    "errors or real-world events.",
    "Developmental responses shown alongside the ecology are "
    "correlations over recorded metrics, not proof of understanding, "
    "adaptation, or emergence.",
    "Human-readable payloads are provenance for inspection; the system "
    "is expected to infer structure from recurrence and consequence.",
    "No network, OS automation, or real-world actuation occurs; "
    "month/year-scale ecology requires explicit governance approval.",
]


class EcologyReportBuilder:
    """Builds the ecology report from a DevelopmentalNursery."""

    def __init__(self, nursery: Any,
                 developmental: Any = None,
                 protolanguage: Any = None,
                 world_model: Any = None) -> None:
        self.nursery = nursery
        self.developmental = developmental
        self.protolanguage = protolanguage
        self.world_model = world_model

    def build(self) -> SessionReport:
        nursery = self.nursery
        snap = nursery.snapshot()
        summary = snap["summary"]
        ecology = snap["ecology"]
        proto_section = self._proto_section()
        world_section = self._world_section()
        report = (
            ExperimentReportBuilder(title="Ecology report")
            .add_metadata(nursery_id=summary["nursery_id"],
                          regime=summary["current_regime"],
                          season=summary["current_season"])
            .add_section("nursery_configuration", snap["config"])
            .add_section("active_regimes", ecology["regimes"])
            .add_section("cycle_summary", ecology["cycles"])
            .add_section("event_distribution",
                         snap["memory"]["event_counts"]
                         or {"none": "no events yet"})
            .add_section("absence_silence_windows", {
                "absence_window_count": summary["absence_window_count"],
                "deprivation": ecology["deprivation"]})
            .add_section("novelty_events", ecology["novelty"])
            .add_section("anomalies", ecology["anomalies"])
            .add_section("scarcity_periods", ecology["scarcity"])
            .add_section("delayed_consequence_groups",
                         ecology["delayed_consequence"])
            .add_section("seasonal_shifts", ecology["seasonality"])
            .add_section("developmental_response_summary",
                         self._developmental_section())
            .add_section("ecology_proto_symbols", proto_section)
            .add_section("ecology_world_model_structures", world_section)
            .add_section("mysterium_trend_during_changes",
                         self._mysterium_section())
        )
        for limitation in ECOLOGY_LIMITATIONS:
            report.add_limitation(limitation)
        return report.build()

    # -- optional cross-layer sections ------------------------------------------------

    def _developmental_section(self) -> Any:
        if self.developmental is None:
            return ["no developmental runtime attached"]
        summary = self.developmental.summary()
        return {
            "current_epoch": summary.get("current_epoch"),
            "growth_status": summary.get("growth_status"),
            "drift_status": summary.get("drift_status"),
            "milestone_count": summary.get("milestone_count"),
            "structural_change_score": summary.get(
                "structural_change_score"),
        }

    def _proto_section(self) -> Any:
        if self.protolanguage is None:
            return ["proto-language not attached"]
        summary = self.protolanguage.summary()
        return {
            "symbol_count": summary.get("symbol_count"),
            "stable_symbol_count": summary.get("stable_symbol_count"),
            "first_stable_symbol": summary.get("first_stable_symbol"),
        }

    def _world_section(self) -> Any:
        if self.world_model is None:
            return ["world model not attached"]
        try:
            counts = self.world_model.graph.node_counts_by_type()
        except AttributeError:
            return ["world model has no graph"]
        return {"node_counts": counts}

    def _mysterium_section(self) -> Any:
        ecology = self.nursery.snapshot()["ecology"]
        return {
            "anomaly_count": ecology["anomalies"]["anomaly_count"],
            "novelty_events": ecology["novelty"]["novelty_events"],
            "note": "anomaly and novelty are the ecology's Mysterium "
                    "drivers; the latent layer regulates the response",
        }

    # -- outputs --------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return self.build().to_dict()

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_markdown(self) -> str:
        return self.build().to_markdown()

    def save(self, json_path: Union[str, Any],
             md_path: Union[str, Any]) -> Dict[str, Any]:
        from ..language.serialization import save_report

        scan = save_report(self.build(), json_path, md_path)
        self.nursery.report_path = str(md_path)
        return {"json": str(json_path), "markdown": str(md_path),
                "claim_guard": scan.to_dict()}
