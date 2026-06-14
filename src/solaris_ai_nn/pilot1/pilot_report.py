"""Pilot-1 report -- the honest, claim-guarded account of a pilot window.

The :class:`PilotReportBuilder` assembles the config, runtime, uptime,
restart/checkpoint history, module health, developmental/ecology/proto-language/
active-perception/hypothesis/LOGOS/auto-regeneration signals, failure modes,
exit criteria, and resource usage into a JSON + Markdown report. Its central
section distinguishes *structural change* from mere *accumulation*. The
Markdown is ClaimGuard-scanned before saving; it never claims consciousness.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PilotReport:
    """The assembled pilot report."""

    report_id: str
    pilot_id: Optional[str]
    sections: Dict[str, Any] = field(default_factory=dict)
    narrative: str = ""
    claim_guard_safe: bool = True
    claim_guard_findings: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "pilot_id": self.pilot_id,
                "timestamp": self.timestamp,
                "claim_guard_safe": self.claim_guard_safe,
                "claim_guard_findings": self.claim_guard_findings,
                "sections": self.sections, "narrative": self.narrative}


@dataclass
class PilotReportBuilder:
    """Builds claim-guarded Pilot-1 reports from collected pilot state."""

    base_dir: str = ".solaris_ai_nn_pilot1"

    def build(self, *, config: Any = None, protocol: Any = None,
              observability: Any = None, resource: Any = None,
              failure_detector: Any = None, exit_decision: Any = None,
              developmental: Optional[Dict[str, Any]] = None,
              restart_runner: Any = None,
              extra: Optional[Dict[str, Any]] = None) -> PilotReport:
        import uuid

        extra = dict(extra or {})
        latest = observability.latest if observability is not None else {}
        cfg_dict = config.to_dict() if config is not None else {}
        structural = self._structural_change(latest, developmental, extra)

        sections: Dict[str, Any] = {
            "pilot_summary": {
                "pilot_id": getattr(config, "pilot_id", None),
                "mode": cfg_dict.get("mode"),
                "authority": cfg_dict.get("authority"),
                "time_label": cfg_dict.get("time_label"),
            },
            "config": cfg_dict,
            "actual_runtime_hours": round(
                (observability.uptime_seconds() / 3600.0)
                if observability is not None else 0.0, 4),
            "target_runtime_days": cfg_dict.get("target_duration_days"),
            "uptime_ratio": float(latest.get("uptime_ratio", 1.0) or 1.0),
            "restart_history": (restart_runner.snapshot()
                                if restart_runner is not None else
                                {"restart_count": latest.get("restart_count",
                                                             0)}),
            "checkpoint_history": {
                "success": int(latest.get("checkpoint_success", 0) or 0),
                "failure": int(latest.get("checkpoint_failure", 0) or 0)},
            "module_health": extra.get("module_health", {}),
            "ecology_exposure": int(latest.get("ecology_event_count", 0) or 0),
            "developmental_epochs": (developmental or {}).get("epochs",
                                                             developmental),
            "memory_layers": extra.get("memory_layers", {}),
            "proto_language_evolution": {
                "symbol_count": int(latest.get("proto_symbol_count", 0) or 0)},
            "active_perception_evolution": {
                "sampling_count": int(latest.get(
                    "active_perception_sampling_count", 0) or 0)},
            "hypotheses": {
                "count": int(latest.get("hypothesis_count", 0) or 0)},
            "logos_complexity": {
                "tension_count": int(latest.get("logos_tension_count", 0)
                                     or 0)},
            "autoregeneration": {
                "degradation_count": int(latest.get(
                    "autoregeneration_degradation_count", 0) or 0)},
            "safety_governance": {
                "safety_incident_count": int(latest.get(
                    "safety_incident_count", 0) or 0),
                "governance_block_count": int(latest.get(
                    "governance_block_count", 0) or 0)},
            "failure_modes": (failure_detector.snapshot()
                              if failure_detector is not None else {}),
            "exit_criteria": (exit_decision.to_dict()
                              if exit_decision is not None else {}),
            "resource_usage": (resource.snapshot()
                               if resource is not None else {}),
            "structural_change_analysis": structural,
            "limitations": [
                "These are operational metrics from a bounded software "
                "process, not evidence of consciousness or understanding.",
                "Structural conclusions require baseline and full-trace "
                "comparison.",
                "Simulated-time runs are not real-time evidence.",
            ],
            "next_pilot_recommendation": extra.get(
                "next_pilot_recommendation",
                "review structural-change analysis, then decide on a longer "
                "governance-approved real soak"),
        }
        narrative = self._narrative(sections)
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(narrative)
        if not scan.safe:
            narrative = ClaimGuard().rewrite(narrative)
        return PilotReport(
            report_id=f"PILOTRPT_{uuid.uuid4().hex[:10]}",
            pilot_id=getattr(config, "pilot_id", None),
            sections=sections, narrative=narrative,
            claim_guard_safe=scan.safe, claim_guard_findings=len(scan.findings))

    def _structural_change(self, latest: Dict[str, Any],
                           developmental: Optional[Dict[str, Any]],
                           extra: Dict[str, Any]) -> Dict[str, Any]:
        """Distinguish structural change from mere accumulation."""
        dev = dict(developmental or {})
        score = float(latest.get("structural_change_score", 0.0) or 0.0)
        symbols = int(latest.get("proto_symbol_count", 0) or 0)
        memory = float(latest.get("memory_size_bytes", 0.0) or 0.0)
        # Evidence of structure: epochs/milestones/phase transitions changed.
        structure_evidence = []
        if dev.get("epoch"):
            structure_evidence.append(f"developmental epoch: {dev['epoch']}")
        if dev.get("milestone_count"):
            structure_evidence.append(
                f"{dev['milestone_count']} milestones reached")
        if score > 0:
            structure_evidence.append(
                f"structural change score {round(score, 6)} > 0")
        if extra.get("phase_transition_candidates"):
            structure_evidence.append("phase-transition candidates present")
        # Evidence of mere accumulation: counts grew without structure signals.
        accumulation_evidence = []
        if memory > 0 and not structure_evidence:
            accumulation_evidence.append(
                "memory grew with no structural-change signal")
        if symbols > 0 and score == 0:
            accumulation_evidence.append(
                "symbol count grew but structural score is flat")
        verdict = ("structural change observed" if structure_evidence
                   else "only accumulation observed" if accumulation_evidence
                   else "insufficient evidence to distinguish")
        return {
            "verdict": verdict,
            "structural_change_score": score,
            "evidence_structure_changed": structure_evidence,
            "evidence_only_accumulation": accumulation_evidence,
        }

    def _narrative(self, sections: Dict[str, Any]) -> str:
        summ = sections["pilot_summary"]
        struct = sections["structural_change_analysis"]
        sg = sections["safety_governance"]
        lines = [
            "# Pilot-1 Report",
            "",
            "This report describes a bounded, low-compute software process "
            "running over a long horizon. It is not a person; it does not "
            "feel, understand, or act in the real world. Operational success "
            "is not evidence of consciousness.",
            "",
            "## Summary",
            f"- pilot: {summ.get('pilot_id')}",
            f"- mode: {summ.get('mode')} ({summ.get('time_label')})",
            f"- authority: {summ.get('authority')} (internal/observe only)",
            f"- actual runtime: {sections['actual_runtime_hours']} h",
            f"- target runtime: {sections['target_runtime_days']} days",
            f"- uptime ratio: {sections['uptime_ratio']}",
            "",
            "## Development vs accumulation",
            f"- verdict: **{struct['verdict']}**",
            f"- structural change score: {struct['structural_change_score']}",
            "- evidence structure changed: "
            + (", ".join(struct["evidence_structure_changed"]) or "none"),
            "- evidence only accumulation: "
            + (", ".join(struct["evidence_only_accumulation"]) or "none"),
            "",
            "## Safety and governance",
            f"- safety incidents: {sg['safety_incident_count']}",
            f"- governance blocks: {sg['governance_block_count']}",
            "",
            "## Exit",
            f"- decision: {sections['exit_criteria'].get('decision', 'n/a')}",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        lines += ["", "## Next pilot recommendation",
                  f"- {sections['next_pilot_recommendation']}"]
        return "\n".join(lines)

    def write(self, report: PilotReport) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "PILOT_REPORT.md")
        json_path = os.path.join(self.base_dir, "PILOT_REPORT.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(report.narrative)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}

    def build_and_write(self, **kwargs: Any) -> PilotReport:
        report = self.build(**kwargs)
        report.sections["report_paths"] = self.write(report)
        return report

    def run_post_pilot_analysis(self, state_dir: Optional[str] = None,
                                ) -> Optional[Dict[str, Any]]:
        """After the final phase, optionally run post-pilot forensics.

        This reads the just-written artifacts read-only and produces the
        post-pilot analysis + research dossier. It never mutates runtime state
        and never starts a run; failures are reported, not raised.
        """
        try:
            from ..post_pilot import PostPilotForensics
        except Exception:
            return None
        try:
            forensics = PostPilotForensics(
                base_dir=self.base_dir,
                state_dir=state_dir or ".solaris_ai_nn_state")
            out = forensics.run()
            return {"summary": out["summary"],
                    "report_paths": out["report_paths"],
                    "dossier_paths": out["dossier_paths"]}
        except Exception as exc:  # analysis must never break a pilot
            return {"error": f"post-pilot analysis failed: {exc}"}
