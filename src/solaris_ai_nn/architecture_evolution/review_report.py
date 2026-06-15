"""Architecture review report -- the claim-guarded "what should we do" account.

The :class:`ArchitectureReviewReportBuilder` assembles the inventory, lifecycle
classification, keep/revise/retest/prune lists, pruning blocks, design debt, ADR
summary, impact summary, roadmap, safety status, limitations, and an operator
review checklist into a JSON + Markdown report. The Markdown is ClaimGuard-
scanned; it recommends, it never implements.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .module_lifecycle import ModuleLifecycleClass as L


@dataclass
class ArchitectureReviewReport:
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
class ArchitectureReviewReportBuilder:
    base_dir: str = ".solaris_ai_nn_architecture"

    def build(self, *, inventory: Any = None,
              lifecycle_assessments: Optional[Dict[str, Any]] = None,
              design_debt: Any = None, adr_snapshot: Optional[Dict] = None,
              impact_summary: Optional[Dict] = None,
              roadmap_summary: Optional[Dict] = None,
              safety_summary: Optional[Dict] = None,
              pruning_blocked: Optional[List[str]] = None,
              extra: Optional[Dict[str, Any]] = None,
              ) -> ArchitectureReviewReport:
        extra = dict(extra or {})
        assessments = lifecycle_assessments or {}

        def _of(klass):
            return sorted(n for n, a in assessments.items()
                          if (a.get("lifecycle_class") if isinstance(a, dict)
                              else getattr(a, "lifecycle_class", "")) == klass)

        keep = _of(L.CORE_KEEP) + _of(L.PROMOTE_TO_CORE) + _of(
            L.EXPERIMENTAL_KEEP)
        revise = _of(L.NEEDS_REVISION)
        retest = _of(L.INSUFFICIENT_EVIDENCE)
        prune_candidates = _of(L.CANDIDATE_FOR_PRUNING) + _of(
            L.CANDIDATE_FOR_QUARANTINE)
        blocked = pruning_blocked or _of(L.SAFETY_CRITICAL_DO_NOT_PRUNE)
        debt_snap = design_debt.snapshot() if hasattr(design_debt, "snapshot") \
            else (design_debt or {})

        sections: Dict[str, Any] = {
            "summary": extra.get(
                "summary",
                "Evidence-based architecture review of a bounded software "
                "system. It recommends what to keep, revise, re-test, or prune "
                "-- it does not modify code."),
            "module_inventory": inventory.snapshot()
            if hasattr(inventory, "snapshot") else (inventory or {}),
            "lifecycle_classification": {
                n: (a.get("lifecycle_class") if isinstance(a, dict)
                    else getattr(a, "lifecycle_class", "unknown"))
                for n, a in assessments.items()},
            "modules_to_keep": keep,
            "modules_to_revise": revise,
            "modules_to_test_again": retest,
            "modules_candidate_for_pruning": prune_candidates,
            "modules_blocked_from_pruning": sorted(set(blocked)),
            "design_debt": debt_snap,
            "adr_summary": adr_snapshot or {},
            "impact_analysis_summary": impact_summary or {},
            "roadmap": roadmap_summary or {},
            "safety_invariant_status": safety_summary or {},
            "limitations": [
                "Recommendations are evidence-scoped and provisional.",
                "Pruning is recommendation-only; no code is modified here.",
                "Safety-critical modules cannot be pruned on performance "
                "evidence alone.",
                "No consciousness, sentience, life, personhood, or free-will "
                "claim is made.",
            ],
            "operator_review_checklist": [
                "review the lifecycle classification and evidence refs",
                "confirm no safety-critical module is proposed for pruning",
                "confirm the roadmap contains no forbidden action",
                "approve/reject each ADR explicitly (recorded, not executed)",
                "any change is implemented manually, outside this system",
            ],
        }
        narrative = self._narrative(sections)
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(narrative)
        if not scan.safe:
            narrative = ClaimGuard().rewrite(narrative)
        return ArchitectureReviewReport(
            report_id=f"ARCHREV_{uuid.uuid4().hex[:10]}", sections=sections,
            narrative=narrative, claim_guard_safe=scan.safe,
            claim_guard_findings=len(scan.findings))

    def _narrative(self, sections: Dict[str, Any]) -> str:
        lines = [
            "# Architecture Review",
            "",
            "This is an evidence-based architecture review of a bounded "
            "software system. It recommends what to keep, revise, re-test, or "
            "prune; it does not modify code, rewrite imports, run Git, or "
            "delete anything. No consciousness, sentience, life, personhood, "
            "or free-will claim is made.",
            "",
            "## Recommendations",
            f"- keep: {sections['modules_to_keep']}",
            f"- revise: {sections['modules_to_revise']}",
            f"- test again: {sections['modules_to_test_again']}",
            f"- pruning candidates: "
            f"{sections['modules_candidate_for_pruning']}",
            f"- blocked from pruning (safety-critical): "
            f"{sections['modules_blocked_from_pruning']}",
            "",
            "## Design debt",
            f"- items: {sections['design_debt'].get('debt_count', 0)} "
            f"(critical: {sections['design_debt'].get('critical_count', 0)})",
            "",
            "## Limitations",
        ]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        lines += ["", "## Operator review checklist"]
        lines += [f"- {c}" for c in sections["operator_review_checklist"]]
        return "\n".join(lines)

    def write(self, report: ArchitectureReviewReport) -> Dict[str, str]:
        os.makedirs(self.base_dir, exist_ok=True)
        md_path = os.path.join(self.base_dir, "ARCHITECTURE_REVIEW.md")
        json_path = os.path.join(self.base_dir, "ARCHITECTURE_REVIEW.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(report.narrative)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path}

    def build_and_write(self, **kwargs: Any) -> ArchitectureReviewReport:
        report = self.build(**kwargs)
        report.sections["report_paths"] = self.write(report)
        return report
