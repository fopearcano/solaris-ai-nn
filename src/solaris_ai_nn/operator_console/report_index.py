"""Report index -- a catalogue of the system's human-facing reports.

:class:`ReportIndexer` finds the known report types (pilot reports, post-pilot
analysis, research report, architecture review, safety reports, assurance case,
Inner MAP snapshot, ops dashboard, membrane/firewall reports, roadmap, ADRs) and
records a summary, a safety status, a recommendation, whether limitations are
present, and whether the report was ClaimGuard-scanned (when detectable). Missing
or corrupted reports are recorded, never hidden.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# (report_type, filename substrings) -- matched against indexed file names.
REPORT_PATTERNS = (
    ("pilot1_report", ("pilot1_report", "full_system_report")),
    ("pilot2_report", ("pilot2_report", "membrane_report")),
    ("pilot3_report", ("pilot3_report", "firewall_report")),
    ("pilot4_readiness_dossier", ("readiness_dossier", "pilot4")),
    ("post_pilot_analysis", ("post_pilot", "forensic")),
    ("research_report", ("research_report",)),
    ("architecture_review", ("architecture_review",)),
    ("safety_invariant_report", ("safety_invariant_report", "safety_dashboard")),
    ("assurance_case", ("assurance_case",)),
    ("inner_map_snapshot", ("inner_map", "innermap")),
    ("ops_dashboard", ("ops_dashboard", "dashboard")),
    ("sensory_membrane_report", ("sensory", "membrane")),
    ("motor_firewall_report", ("motor", "firewall")),
    ("roadmap", ("roadmap",)),
    ("adr", ("adr_", "adr.json", "decision_record")),
)


def _classify(name: str) -> Optional[str]:
    low = name.lower()
    for report_type, hints in REPORT_PATTERNS:
        if any(h in low for h in hints):
            return report_type
    return None


@dataclass
class ReportRecord:
    report_id: str
    report_type: str
    path: str
    created_or_modified: float
    summary: Optional[str] = None
    safety_status: Optional[str] = None
    recommendation: Optional[str] = None
    limitations_present: bool = False
    claim_guard_scanned: bool = False
    corrupted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ReportIndex:
    records: List[ReportRecord] = field(default_factory=list)

    def add(self, record: ReportRecord) -> None:
        self.records.append(record)

    def by_type(self, report_type: str) -> List[ReportRecord]:
        return [r for r in self.records if r.report_type == report_type]

    def corrupted(self) -> List[ReportRecord]:
        return [r for r in self.records if r.corrupted]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_count": len(self.records),
            "corrupted_count": len(self.corrupted()),
            "records": [r.to_dict() for r in self.records],
        }


@dataclass
class ReportIndexer:
    """Indexes known reports across the local directories."""

    directories: List[str] = field(default_factory=list)

    def index(self) -> ReportIndex:
        from .artifact_index import DEFAULT_DIRECTORIES

        dirs = self.directories or list(DEFAULT_DIRECTORIES)
        index = ReportIndex()
        seq = 0
        for directory in dirs:
            if not directory or not os.path.isdir(directory):
                continue
            for root, _dirs, files in os.walk(directory):
                for name in sorted(files):
                    report_type = _classify(name)
                    if report_type is None:
                        continue
                    seq += 1
                    index.add(self._index_report(
                        f"RPT_{seq:04d}", report_type,
                        os.path.join(root, name)))
        return index

    def _index_report(self, report_id: str, report_type: str,
                      path: str) -> ReportRecord:
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            return ReportRecord(report_id=report_id, report_type=report_type,
                                path=path, created_or_modified=0.0,
                                corrupted=True)
        summary = safety_status = recommendation = None
        limitations = claim_guard = corrupted = False
        if path.lower().endswith(".json"):
            data, corrupted = self._load_json(path)
            if isinstance(data, dict):
                summary = self._first_str(
                    data, ("summary", "description", "title", "headline"))
                safety_status = self._first_str(
                    data, ("safety_status", "status", "overall_status"))
                recommendation = self._first_str(
                    data, ("recommendation", "recommended_action", "decision"))
                blob = json.dumps(data).lower()
                limitations = "limitation" in blob or "caveat" in blob
                claim_guard = ("claim_guard" in blob or "claimguard" in blob
                               or "claim_guard_safe" in blob)
        else:
            limitations, claim_guard = self._scan_text(path)
        return ReportRecord(
            report_id=report_id, report_type=report_type, path=path,
            created_or_modified=mtime, summary=summary,
            safety_status=safety_status, recommendation=recommendation,
            limitations_present=limitations, claim_guard_scanned=claim_guard,
            corrupted=corrupted)

    @staticmethod
    def _load_json(path: str):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh), False
        except (OSError, json.JSONDecodeError):
            return None, True

    @staticmethod
    def _scan_text(path: str):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read(20_000).lower()
            return ("limitation" in text or "caveat" in text,
                    "claim-guard" in text or "claimguard" in text)
        except OSError:
            return False, False

    @staticmethod
    def _first_str(data: Dict[str, Any], keys) -> Optional[str]:
        for key in keys:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value[:300]
        return None
