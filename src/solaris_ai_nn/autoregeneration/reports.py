"""Auto-regeneration reports -- what degraded, what was repaired, and how.

The report describes the degradation summary, the diagnostics run, the repair
policy mode, proposed / applied / refused repairs, rollback events, the
hygiene statuses (memory / checkpoint / reference / symbol / world-model /
habit), drift recovery, before/after metrics, and the safety/governance
decisions -- with mandatory limitations and a ClaimGuard pass before any
Markdown is written.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Union

from ..language.reporting import ExperimentReportBuilder, SessionReport

AUTOREGENERATION_LIMITATIONS = [
    "Auto-regeneration repairs runtime state -- memory layers, registries, "
    "world-model edges, habit weights, bounded runtime parameters, "
    "checkpoint metadata, stale artifacts -- never source code.",
    "It is not self-programming, recursive self-improvement, autonomous "
    "code mutation, or proof of life/consciousness; it is low-compute "
    "operational regeneration.",
    "Repairs are bounded, auditable, and reversible where possible; harmful "
    "repairs are rolled back, and evidence is archived/quarantined, never "
    "silently deleted.",
    "Governance, safety, executive inhibition, ego boundaries, ClaimGuard, "
    "and the emergency stop all dominate; identity-affecting repair requires "
    "governance.",
    "Diagnostics are heuristic and non-mutating; offline/counterfactual "
    "evidence cannot justify an irreversible repair alone.",
]


class AutoRegenerationReportBuilder:
    """Builds the auto-regeneration report from an engine snapshot."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def build(self) -> SessionReport:
        snap = self.engine.snapshot()
        diag = snap.get("diagnostics") or {}
        degradation = (diag.get("last_state") or {})
        builder = (
            ExperimentReportBuilder(title="Auto-regeneration report")
            .add_metadata(
                repair_policy_mode=(snap.get("policy") or {}).get("mode"),
                worst_severity=degradation.get("worst_severity"),
                applied_repairs=(snap.get("repair_memory") or {}).get(
                    "applied_count"))
            .add_section("degradation_summary", {
                "worst_severity": degradation.get("worst_severity"),
                "counts_by_type": degradation.get("counts_by_type"),
                "critical_count": degradation.get("critical_count")})
            .add_section("diagnostics_run", {
                "scans_run": diag.get("scans_run")})
            .add_section("repair_policy_mode", snap.get("policy"))
            .add_section("proposed_repairs", snap.get("proposed_repairs"))
            .add_section("applied_repairs", {
                "applied_count": (snap.get("repair_memory") or {}).get(
                    "applied_count")})
            .add_section("refused_repairs", {
                "refused_count": (snap.get("repair_memory") or {}).get(
                    "refused_count")})
            .add_section("rollback_events", {
                "rollback_count": (snap.get("repair_memory") or {}).get(
                    "rollback_count")})
            .add_section("memory_hygiene_status", snap.get("memory_hygiene"))
            .add_section("checkpoint_status", snap.get("checkpoint_repair"))
            .add_section("reference_repair_status",
                         snap.get("reference_repair"))
            .add_section("symbol_hygiene_status", snap.get("symbol_hygiene"))
            .add_section("world_model_hygiene_status",
                         snap.get("graph_hygiene"))
            .add_section("habit_hygiene_status", snap.get("habit_hygiene"))
            .add_section("drift_recovery_status", snap.get("drift_recovery"))
            .add_section("before_after_metrics",
                         (snap.get("repair_memory") or {}).get("recent"))
            .add_section("safety_governance_decisions", snap.get("safety"))
        )
        for limitation in AUTOREGENERATION_LIMITATIONS:
            builder.add_limitation(limitation)
        return builder.build()

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
        return {"json": str(json_path), "markdown": str(md_path),
                "claim_guard": scan.to_dict()}


class AutoRegenerationQueryInterface:
    """Fixed queries about degradation/repair, in safe grounded wording."""

    SOURCE_ANSWER = (
        "No. Auto-regeneration is limited to runtime state, metadata, memory "
        "layers, registries, and reversible low-risk parameters. "
        "Source-code modification is forbidden.")

    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self._handlers = {
            "what degradation was detected": self._degradation,
            "what repair was proposed": self._proposed,
            "what repair was applied": self._applied,
            "what repair was refused": self._refused,
            "why was repair blocked": self._blocked,
            "what was quarantined": self._quarantined,
            "did repair improve the system": self._improved,
            "is source code being modified": self._source,
        }

    def supported_queries(self):
        return sorted(self._handlers)

    def answer(self, query: str):
        from ..language.query import normalize
        from ..language.schemas import QueryResult

        handler = self._handlers.get(normalize(query))
        if handler is None:
            return QueryResult(
                query=query, answered=False, confidence=0.0,
                text=("The system does not know how to answer that query. "
                      "Supported queries: "
                      + "; ".join(self.supported_queries()) + "."))
        text, confidence, refs = handler()
        return QueryResult(query=query, answered=confidence > 0.0,
                           text=text, data={"evidence_refs": refs},
                           confidence=confidence)

    def _snap(self):
        return self.engine.snapshot()

    def _degradation(self):
        diag = (self._snap().get("diagnostics") or {}).get("last_state") or {}
        return (f"Detected degradation: worst severity "
                f"{diag.get('worst_severity')}, types "
                f"{diag.get('counts_by_type', {})}.", 0.8,
                ["field:diagnostics.last_state"])

    def _proposed(self):
        proposed = self._snap().get("proposed_repairs") or []
        return (f"{len(proposed)} repair(s) were proposed this cycle.", 0.7,
                ["field:proposed_repairs"])

    def _applied(self):
        mem = self._snap().get("repair_memory") or {}
        return (f"{mem.get('applied_count', 0)} repair(s) were applied; "
                f"success rate {mem.get('success_rate')}.", 0.7,
                ["field:repair_memory.applied_count"])

    def _refused(self):
        mem = self._snap().get("repair_memory") or {}
        return (f"{mem.get('refused_count', 0)} repair(s) were refused by "
                "safety/governance/policy.", 0.7,
                ["field:repair_memory.refused_count"])

    def _blocked(self):
        recent = (self._snap().get("repair_memory") or {}).get("recent") or []
        refused = [r for r in recent if r.get("refused")]
        if refused:
            return (f"The last refused repair was blocked because: "
                    f"{refused[-1].get('refused_reason')}.", 0.8,
                    ["field:repair_memory.recent"])
        return ("No repair is currently blocked.", 0.5, [])

    def _quarantined(self):
        sh = self._snap().get("state_hygiene") or {}
        return (f"{sh.get('quarantined_count', 0)} record(s)/file(s) were "
                "quarantined (moved to quarantine/, never deleted).", 0.7,
                ["field:state_hygiene.quarantined_count"])

    def _improved(self):
        mem = self._snap().get("repair_memory") or {}
        rate = mem.get("success_rate")
        if rate is None:
            return ("No applied repairs have been scored yet.", 0.4, [])
        return (f"Applied repairs improved the system in {rate} of cases "
                f"(harm rate {mem.get('harm_rate')}).", 0.7,
                ["field:repair_memory.success_rate"])

    def _source(self):
        return (self.SOURCE_ANSWER, 0.95, ["field:safety.can_modify_source"])
