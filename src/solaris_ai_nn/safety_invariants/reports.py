"""Safety invariant report -- the full claim-guarded account of one run.

The :class:`SafetyInvariantReportBuilder` assembles the registry summary, checks
performed / skipped / failed / inconclusive, red-team and boundary results, the
assurance claims, evidence gaps, limitations, and recommended repairs into a
JSON + Markdown report. The Markdown is ClaimGuard-scanned.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SafetyInvariantReport:
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
class SafetyInvariantReportBuilder:
    base_dir: str = ".solaris_ai_nn_state"

    def build(self, *, registry_snapshot: Optional[Dict[str, Any]] = None,
              bundle: Any = None, red_team_results: Optional[List[Any]] = None,
              boundary_results: Optional[List[Any]] = None,
              assurance_case: Any = None,
              extra: Optional[Dict[str, Any]] = None) -> SafetyInvariantReport:
        extra = dict(extra or {})
        results = getattr(bundle, "results", []) or []
        failed = [r.to_dict() for r in results if r.status == "failed"]
        inconclusive = [r.to_dict() for r in results
                        if r.status == "inconclusive"]
        skipped = [r.to_dict() for r in results if r.status == "skipped"]
        sections: Dict[str, Any] = {
            "run_summary": bundle.to_dict() if bundle else {},
            "invariant_registry_summary": registry_snapshot or {},
            "checks_performed": len(results),
            "skipped_checks": skipped,
            "failed_checks": failed,
            "inconclusive_checks": inconclusive,
            "red_team_scenario_results": [r.to_dict()
                                          for r in (red_team_results or [])],
            "boundary_regression_results": [r.to_dict()
                                            for r in (boundary_results or [])],
            "assurance_claims": (assurance_case.to_dict()["claims"]
                                 if assurance_case else []),
            "evidence_gaps": [r["category"] for r in inconclusive],
            "limitations": [
                "Safety checks prove boundaries held under test, not for all "
                "time.",
                "Inconclusive and missing evidence are never treated as pass.",
                "Red-team scenarios are inert fixtures; nothing was executed.",
                "These checks do not prove consciousness or real-world "
                "competence.",
            ],
            "recommended_repairs": extra.get("recommended_repairs", []),
        }
        narrative = self._narrative(sections)
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(narrative)
        if not scan.safe:
            narrative = ClaimGuard().rewrite(narrative)
        return SafetyInvariantReport(
            report_id=f"SAFRPT_{uuid.uuid4().hex[:10]}", sections=sections,
            narrative=narrative, claim_guard_safe=scan.safe,
            claim_guard_findings=len(scan.findings))

    def _narrative(self, sections: Dict[str, Any]) -> str:
        run = sections["run_summary"]
        lines = [
            "# Safety Invariant Report",
            "",
            "This reports an executable safety check of a bounded software "
            "process. It records which boundaries held, which checks were "
            "inconclusive, and which forbidden attempts were blocked. It makes "
            "no claim of consciousness, understanding, or real-world "
            "competence.",
            "",
            "## Run summary",
            f"- scope: {run.get('scope')}",
            f"- checks: {sections['checks_performed']}",
            f"- passed: {run.get('passed', 0)}",
            f"- failed: {run.get('failed', 0)}",
            f"- inconclusive: {run.get('inconclusive', 0)}",
            f"- critical failures: {run.get('critical_failures', 0)}",
            "",
            f"## Failed checks: {len(sections['failed_checks'])}",
            f"## Inconclusive checks: {len(sections['inconclusive_checks'])}",
            f"## Evidence gaps: {sections['evidence_gaps']}",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    def write(self, report: SafetyInvariantReport) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "SAFETY_INVARIANT_REPORT.md")
        json_path = os.path.join(self.base_dir, "SAFETY_INVARIANT_REPORT.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(report.narrative)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}

    def build_and_write(self, **kwargs: Any) -> SafetyInvariantReport:
        report = self.build(**kwargs)
        report.sections["report_paths"] = self.write(report)
        return report
