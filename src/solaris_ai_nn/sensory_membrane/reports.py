"""Sensory membrane report -- a claim-guarded summary of read-only ingestion.

The :class:`SensoryMembraneReportBuilder` assembles registered sources, source
health, read-only validation, event/modality counts, malformed/dropped/absence
counts, grounding and provenance summaries, and any safety violations into a
Markdown + JSON report. The Markdown is ClaimGuard-scanned before saving.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SensoryMembraneReport:
    report_id: str
    sections: Dict[str, Any] = field(default_factory=dict)
    narrative: str = ""
    claim_guard_safe: bool = True
    claim_guard_findings: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"report_id": self.report_id, "timestamp": self.timestamp,
                "claim_guard_safe": self.claim_guard_safe,
                "claim_guard_findings": self.claim_guard_findings,
                "sections": self.sections, "narrative": self.narrative}


@dataclass
class SensoryMembraneReportBuilder:
    """Builds the claim-guarded sensory membrane report."""

    state_dir: Optional[str] = None

    def build(self, runtime: Any) -> SensoryMembraneReport:
        snap = runtime.snapshot()
        summary = snap.get("summary", {})
        registry = snap.get("registry", {})
        sources = registry.get("sources", {})
        modality_counts = self._modality_counts(runtime)
        sections: Dict[str, Any] = {
            "registered_sources": [
                {"source_id": sid, "type": s.get("config", {}).get(
                    "source_type"), "status": s.get("status"),
                 "simulated": s.get("config", {}).get("is_simulated")}
                for sid, s in sources.items()],
            "source_health": {sid: s.get("status")
                              for sid, s in sources.items()},
            "read_only_validation": {
                sid: s.get("read_only_validated")
                for sid, s in sources.items()},
            "event_counts_by_source": {
                sid: s.get("event_count", 0) for sid, s in sources.items()},
            "event_counts_by_modality": modality_counts,
            "malformed_event_count": summary.get("malformed_events", 0),
            "dropped_event_count": summary.get("dropped_events", 0),
            "absence_events": summary.get("absence_events", 0),
            "novelty_events": snap.get("grounding", {}).get(
                "proto_symbol_candidate_count", 0),
            "grounding_summary": snap.get("grounding", {}),
            "provenance_summary": snap.get("provenance", {}),
            "safety_violations": snap.get("safety", {}).get("rejected_count",
                                                           0),
            "read_only": summary.get("read_only", True),
            "limitations": [
                "All sources are read-only; the system never acts on the "
                "world.",
                "Camera/audio are metadata-only; no OCR/ASR/image analysis.",
                "Environmental input is never an operator command.",
                "Grounding is operational association, not understanding.",
            ],
        }
        narrative = self._narrative(sections, summary)
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(narrative)
        if not scan.safe:
            narrative = ClaimGuard().rewrite(narrative)
        return SensoryMembraneReport(
            report_id=f"SMR_{uuid.uuid4().hex[:10]}", sections=sections,
            narrative=narrative, claim_guard_safe=scan.safe,
            claim_guard_findings=len(scan.findings))

    @staticmethod
    def _modality_counts(runtime: Any) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for record in getattr(getattr(runtime, "grounding", None),
                              "records", []) or []:
            counts[record.modality] = counts.get(record.modality, 0) + 1
        return counts

    def _narrative(self, sections: Dict[str, Any],
                   summary: Dict[str, Any]) -> str:
        lines = [
            "# Sensory Membrane Report",
            "",
            "This describes a read-only sensory membrane. The world may enter "
            "the system as environmental input; the system never acts on the "
            "world. Environmental input is not an operator command.",
            "",
            "## Sources",
            f"- registered: {len(sections['registered_sources'])}",
            f"- read-only: {sections['read_only']}",
            f"- safety violations: {sections['safety_violations']}",
            "",
            "## Events",
            f"- total: {summary.get('total_events', 0)}",
            f"- by modality: {sections['event_counts_by_modality']}",
            f"- malformed: {sections['malformed_event_count']}",
            f"- dropped: {sections['dropped_event_count']}",
            f"- absence: {sections['absence_events']}",
            f"- provenance completeness: "
            f"{summary.get('provenance_completeness', 0.0)}",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    def write(self, report: SensoryMembraneReport,
              state_dir: Optional[str] = None) -> Dict[str, str]:
        base = state_dir or self.state_dir or "."
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "SENSORY_MEMBRANE_REPORT.md")
        json_path = os.path.join(base, "SENSORY_MEMBRANE_REPORT.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(report.narrative)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}

    def build_and_write(self, runtime: Any,
                        state_dir: Optional[str] = None,
                        ) -> SensoryMembraneReport:
        report = self.build(runtime)
        paths = self.write(report, state_dir)
        report.sections["report_paths"] = paths
        if hasattr(runtime, "report_path"):
            runtime.report_path = paths["json"]
        else:
            setattr(runtime, "report_path", paths["json"])
        return report
