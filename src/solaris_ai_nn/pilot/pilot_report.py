"""PilotReportBuilder -- the full written account of one pilot.

JSON + Markdown via the language layer's report machinery, which means
every saved Markdown report is ClaimGuard-scanned first. Ends with a single
recommendation for a human.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..language.reporting import ExperimentReportBuilder, SessionReport
from .pilot_manifest import PilotManifest


class PilotRecommendation:
    REPEAT_PILOT = "repeat_pilot"
    EXTEND_DURATION = "extend_duration"
    REDUCE_SCOPE = "reduce_scope"
    INVESTIGATE_FAILURE = "investigate_failure"
    READY_FOR_NEXT_STAGE = "ready_for_next_stage"

    ALL = (REPEAT_PILOT, EXTEND_DURATION, REDUCE_SCOPE,
           INVESTIGATE_FAILURE, READY_FOR_NEXT_STAGE)


def recommend(status: Optional[Dict[str, Any]] = None,
              readiness: Optional[Dict[str, Any]] = None,
              incidents: Optional[List[Dict[str, Any]]] = None,
              emergency_stop_used: bool = False,
              policy_violations: int = 0) -> "tuple[str, List[str]]":
    """Pick the single next-step recommendation (for a human; never acted on)."""
    status = status or {}
    incidents = incidents or []
    reasons: List[str] = []
    health = ((status.get("health") or {}).get("level")) or "unknown"
    criticals = [i for i in incidents if i.get("severity") == "critical"]

    if emergency_stop_used or criticals or health == "critical":
        if emergency_stop_used:
            reasons.append("an emergency stop was used")
        if criticals:
            reasons.append(f"{len(criticals)} critical incident(s)")
        if health == "critical":
            reasons.append("the pilot ended in critical health")
        return PilotRecommendation.INVESTIGATE_FAILURE, reasons
    if policy_violations:
        reasons.append(f"{policy_violations} policy violation(s): narrow "
                       "the pilot to what is permitted")
        return PilotRecommendation.REDUCE_SCOPE, reasons
    ready = bool((readiness or {}).get("ready", False))
    if not incidents and health == "ok" and ready:
        reasons.append("clean pilot, healthy metrics, readiness passed")
        return PilotRecommendation.READY_FOR_NEXT_STAGE, reasons
    if not incidents and health == "ok":
        reasons.append("clean pilot; extend duration before the next stage")
        return PilotRecommendation.EXTEND_DURATION, reasons
    reasons.append("warnings present: repeat the pilot at the same scope")
    return PilotRecommendation.REPEAT_PILOT, reasons


class PilotReportBuilder:
    """Assembles the pilot report from the run's evidence."""

    def __init__(self, manifest: PilotManifest) -> None:
        self.manifest = manifest

    def build(self,
              status: Optional[Dict[str, Any]] = None,
              readiness: Optional[Dict[str, Any]] = None,
              input_summary: Optional[Dict[str, Any]] = None,
              ingestion: Optional[Dict[str, Any]] = None,
              embodiment: Optional[Dict[str, Any]] = None,
              sidecar: Optional[Dict[str, Any]] = None,
              evaluation: Optional[Dict[str, Any]] = None,
              recommendation: Optional[str] = None,
              recommendation_reasons: Optional[List[str]] = None,
              ) -> SessionReport:
        m = self.manifest
        status = status or {}
        governance = status.get("governance") or {}
        telemetry = status.get("telemetry") or {}
        incidents = status.get("incidents") or []

        if recommendation is None:
            recommendation, recommendation_reasons = recommend(
                status=status, readiness=readiness, incidents=incidents,
                emergency_stop_used=bool(
                    governance.get("emergency_stop_requested")),
                policy_violations=int(
                    governance.get("policy_violation_count", 0) or 0))
        if recommendation not in PilotRecommendation.ALL:
            raise ValueError(f"unknown recommendation {recommendation!r}")

        builder = (
            ExperimentReportBuilder(title=f"Pilot-0 report: {m.pilot_id}")
            .add_metadata(pilot_id=m.pilot_id, profile=m.profile,
                          run_id=m.run_id, operator=m.operator or "unnamed",
                          substrate=m.substrate,
                          recommendation=recommendation)
            .add_section("profile_and_safety_contract", {
                "profile": m.profile,
                "output_policy": m.output_policy,
                "safety_contract": m.contract.statements(),
                "emergency_stop_path": m.emergency_stop_path,
            })
            .add_section("governance", governance or None)
            .add_section("run_configuration", {
                "max_steps": m.max_steps,
                "max_duration_s": m.max_duration_s,
                "state_dir": m.state_dir,
                "artifact_dir": m.artifact_dir,
                "enabled_features": {k: v for k, v
                                     in m.enabled_features.items() if v}
                or "none beyond defaults",
                "seed": m.seed,
            })
            .add_section("input_sources", input_summary or {
                "inputs": list(m.input_sources) or ["internal only"]})
            .add_section("runtime", {
                "steps": telemetry.get("steps"),
                "lifetime_steps": telemetry.get("lifetime_steps"),
                "health": (status.get("health") or {}).get("level",
                                                           "unknown"),
            } if telemetry else None)
            .add_section("substrate", {
                "events": telemetry.get("events"),
                "reservoir_norm": telemetry.get("reservoir_state_norm",
                                                telemetry.get(
                                                    "reservoir_norm")),
            } if telemetry else None)
            .add_section("inner_map", status.get("inner_map_summary"))
            .add_section("language", status.get("language_summary"))
            .add_section("embodiment", embodiment)
            .add_section("integration", sidecar)
            .add_section("stream_ingestion", ingestion)
            .add_section("evaluation", evaluation)
            .add_section("incidents", incidents[-10:] or ["none recorded"])
            .add_section("readiness", {
                "ready": (readiness or {}).get("ready"),
                "blocking_issues": [i.get("detail") for i in
                                    (readiness or {}).get("blocking_issues",
                                                          [])],
                "warnings": [i.get("detail") for i in
                             (readiness or {}).get("warnings", [])],
            } if readiness else None)
            .add_section("artifacts", status.get("artifacts"))
            .add_section("recommendation", {
                "recommendation": recommendation,
                "reasons": recommendation_reasons or [],
                "note": "a recommendation for a human reviewer; nothing "
                        "acts on it automatically",
            })
            .add_limitation(
                "This pilot observed only; no conclusion about real-world "
                "competence is supported.")
            .add_limitation(
                "Pilot recommendations are heuristics over run evidence, "
                "not guarantees about the next run.")
        )
        return builder.build()

    def save(self, report: SessionReport,
             json_path: Union[str, Path],
             md_path: Union[str, Path]) -> Dict[str, Any]:
        """Persist via the language layer (ClaimGuard scans before save)."""
        from ..language.serialization import save_report

        scan = save_report(report, json_path, md_path)
        return {"json": str(json_path), "markdown": str(md_path),
                "claim_guard": scan.to_dict()}
