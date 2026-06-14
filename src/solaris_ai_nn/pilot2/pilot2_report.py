"""Pilot-2 report -- a claim-guarded account of read-only environmental exposure.

The :class:`Pilot2ReportBuilder` assembles config, source preflight, curated
sources, exposure schedule, source reliability, sensory event/provenance
summary, grounding analysis, nursery-vs-sensory comparison, and per-layer
findings into a JSON + Markdown report. The Markdown is ClaimGuard-scanned;
it never claims consciousness and uses cautious comparative language.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Pilot2Report:
    report_id: str
    pilot2_id: Optional[str]
    sections: Dict[str, Any] = field(default_factory=dict)
    narrative: str = ""
    claim_guard_safe: bool = True
    claim_guard_findings: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "pilot2_id": self.pilot2_id,
                "timestamp": self.timestamp,
                "claim_guard_safe": self.claim_guard_safe,
                "claim_guard_findings": self.claim_guard_findings,
                "sections": self.sections, "narrative": self.narrative}


@dataclass
class Pilot2ReportBuilder:
    base_dir: str = ".solaris_ai_nn_pilot2"

    def build(self, *, config: Any = None, preflight: Optional[Dict] = None,
              curation: Optional[Dict] = None, schedule: Optional[Dict] = None,
              reliability: Any = None, membrane: Optional[Dict] = None,
              grounding: Any = None, comparison: Optional[Dict] = None,
              extra: Optional[Dict[str, Any]] = None) -> Pilot2Report:
        extra = dict(extra or {})
        cfg = config.to_dict() if config is not None else {}
        membrane = dict(membrane or {})
        sections: Dict[str, Any] = {
            "pilot2_summary": {
                "pilot2_id": getattr(config, "pilot2_id", None),
                "mode": cfg.get("mode"),
                "authority": cfg.get("authority"),
                "source_mode": cfg.get("source_mode"),
                "time_label": cfg.get("time_label"),
            },
            "config": cfg,
            "source_preflight": preflight or {},
            "curated_sources": curation or {},
            "exposure_schedule": schedule or {},
            "source_reliability": (reliability.snapshot()
                                   if hasattr(reliability, "snapshot")
                                   else (reliability or {})),
            "sensory_event_summary": {
                "total_events": membrane.get("total_events", 0),
                "by_modality": membrane.get("event_count_by_modality", {}),
                "malformed_events": membrane.get("malformed_events", 0)},
            "provenance_completeness": membrane.get("provenance_completeness",
                                                   1.0),
            "grounding_analysis": (grounding.snapshot()
                                   if hasattr(grounding, "snapshot")
                                   else (grounding or {})),
            "nursery_vs_sensory_comparison": comparison or {},
            "proto_language_findings": extra.get("proto_language_findings", {}),
            "world_model_findings": extra.get("world_model_findings", {}),
            "active_perception_findings": extra.get(
                "active_perception_findings", {}),
            "hypothesis_findings": extra.get("hypothesis_findings", {}),
            "logos_findings": extra.get("logos_findings", {}),
            "autoregeneration_findings": extra.get(
                "autoregeneration_findings", {}),
            "safety_governance_findings": extra.get(
                "safety_governance_findings", {}),
            "resource_usage": extra.get("resource_usage", {}),
            "limitations": [
                "Pilot-2 is read-only; the system never acts on the world.",
                "Differences are observed associations, not proven causes.",
                "Grounding is operational association, not understanding.",
                "Simulated/fixture exposure is not real-time evidence.",
                "No consciousness, sentience, or life is claimed.",
            ],
            "next_recommendation": extra.get(
                "next_recommendation",
                "review grounding and reliability, then decide via the "
                "Pilot-2 decision gate"),
        }
        narrative = self._narrative(sections)
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(narrative)
        if not scan.safe:
            narrative = ClaimGuard().rewrite(narrative)
        return Pilot2Report(
            report_id=f"P2RPT_{uuid.uuid4().hex[:10]}",
            pilot2_id=getattr(config, "pilot2_id", None), sections=sections,
            narrative=narrative, claim_guard_safe=scan.safe,
            claim_guard_findings=len(scan.findings))

    def _narrative(self, sections: Dict[str, Any]) -> str:
        summ = sections["pilot2_summary"]
        grounding = sections["grounding_analysis"]
        comparison = sections["nursery_vs_sensory_comparison"]
        lines = [
            "# Pilot-2 Report",
            "",
            "This reports a read-only environmental exposure of a bounded "
            "software process. The environment entered the system through "
            "approved read-only sources; the system never acted on the "
            "environment, and sensory input was never an operator command. "
            "No consciousness, sentience, understanding, or life is claimed.",
            "",
            "## Summary",
            f"- pilot: {summ.get('pilot2_id')}",
            f"- mode: {summ.get('mode')} ({summ.get('time_label')})",
            f"- source mode: {summ.get('source_mode')}",
            f"- authority: {summ.get('authority')} (read-only; no actuation)",
            "",
            "## Sensory exposure",
            f"- total events: "
            f"{sections['sensory_event_summary'].get('total_events')}",
            f"- provenance completeness: "
            f"{sections['provenance_completeness']}",
            "",
            "## Grounding",
            f"- best grounding quality: "
            f"{grounding.get('best_quality', 'unsupported')}",
            f"- has grounding evidence: "
            f"{grounding.get('has_grounding_evidence', False)}",
            "",
            "## Nursery vs sensory comparison",
            f"- {comparison.get('disclaimer', 'no comparison available')}",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        lines += ["", "## Next recommendation",
                  f"- {sections['next_recommendation']}"]
        return "\n".join(lines)

    def write(self, report: Pilot2Report) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "PILOT2_REPORT.md")
        json_path = os.path.join(self.base_dir, "PILOT2_REPORT.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(report.narrative)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}

    def build_and_write(self, **kwargs: Any) -> Pilot2Report:
        report = self.build(**kwargs)
        report.sections["report_paths"] = self.write(report)
        return report
