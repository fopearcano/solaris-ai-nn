"""Post-merge assimilation reports -- local research documents, ClaimGuard-scanned.

:class:`PostMergeAssimilationReportBuilder` writes the assimilation report plus
the baseline registry / comparison / regression / module-status / rollback /
follow-up documents. Every report states explicitly that no source was modified,
no Git command was run, no GitHub call was made, no PR was created/approved/
merged, no validation command was executed automatically, no external agent was
run, this is post-merge evidence assimilation only, and no consciousness/life/
agency claim is made. The Markdown is scanned by ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "No source code was modified.",
    "No Git command was run.",
    "No GitHub call was made.",
    "No pull request was created, approved, or merged.",
    "No validation command was executed automatically.",
    "No external coding agent was run.",
    "This is post-merge evidence assimilation only.",
    "No consciousness/life/agency claim is made.",
)

_LIMITATIONS = (
    "Reads operator-provided local artifacts only; it never calls GitHub or "
    "runs Git.",
    "Operator-provided validation is evidence, not proof.",
    "A safety regression dominates positive metrics; a critical regression "
    "blocks validation.",
    "Missing critical evidence blocks validation and stays visible.",
    "The baseline registry is append-only; failed/blocked baselines remain "
    "visible.",
)


@dataclass
class PostMergeAssimilationReportBuilder:
    """Builds the post-merge report set (JSON + claim-guarded Markdown docs)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.post_merge_status()
        parent = rt.registry.get(rt.parent_baseline_id)
        sections: Dict[str, Any] = {
            "purpose": ("assimilate operator-provided local evidence after an "
                        "external human merge and update research baselines -- "
                        "not a merge, not a release, not self-modification"),
            "merge_manifest_summary": (rt.manifest.to_dict() if rt.manifest
                                       else {}),
            "candidate_baseline": (rt.candidate.to_dict() if rt.candidate
                                   else {}),
            "parent_baseline": parent.to_dict() if parent else {},
            "validation_ingest_summary": rt.validation,
            "evidence_assimilation": rt.evidence,
            "baseline_comparison": rt.comparison,
            "regression_watch": rt.regression,
            "module_status_recommendations": rt.module_status,
            "rollback_watch": rt.rollback,
            "followup_queue": rt.followup,
            "missing_evidence": rt.validation.get("missing_required", []),
            "unresolved_blockers": (rt.candidate.unresolved_blockers
                                    if rt.candidate else []),
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "limitations": list(_LIMITATIONS),
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_main(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_main(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        lines = [
            "# Post-Merge Assimilation Report", "",
            "_A human changed the code externally; this report assimilates the "
            "operator-provided local evidence and asks what that change did to "
            "the experimental architecture. It reads local artifacts and writes "
            "reports ONLY: no source change, no Git, no GitHub, no PR "
            "create/approve/merge, and no validation command is executed._", "",
            f"- candidate baseline: {status['candidate_baseline_id']} -> "
            f"**{status['candidate_baseline_status']}**",
            f"- baselines registered: {status['baseline_record_count']} "
            f"(validated {status['validated_baseline_count']}, blocked "
            f"{status['blocked_baseline_count']})",
            f"- validation artifacts: {status['validation_artifact_count']} "
            f"(missing {status['missing_validation_artifact_count']})",
            f"- baseline comparison: {sections['baseline_comparison'].get('overall')}",
            f"- regressions: {status['baseline_regression_count']} "
            f"(critical {status['critical_regression_count']})",
            f"- module status recommendation: "
            f"{status['module_status_recommendation']}",
            f"- rollback watch: {status['rollback_recommendation_status']} "
            f"({status['rollback_watch_trigger_count']} trigger(s))",
            f"- follow-up queue: {status['followup_queue_count']} item(s)",
            "",
            "## Unresolved blockers", "",
        ]
        blockers = sections["unresolved_blockers"]
        lines += [f"- {b}" for b in blockers] if blockers else ["- none"]
        lines += ["", "## Missing evidence", ""]
        missing = sections["missing_evidence"]
        lines += [f"- {m}" for m in missing] if missing else ["- none"]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in sections["what_this_does_not_do"]]
        lines += ["", "## Limitations", ""]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    @staticmethod
    def _claim_guard_safe(text: str) -> bool:
        try:
            from ..governance.compliance import ClaimGuard

            return ClaimGuard().scan_text(text).safe
        except Exception:
            return True

    @staticmethod
    def _guard(text: str) -> str:
        try:
            from ..governance.compliance import ClaimGuard

            guard = ClaimGuard()
            if not guard.scan_text(text).safe:
                return guard.rewrite(text)
        except Exception:
            pass
        return text

    def _sub_reports(self, sections: Dict[str, Any]) -> Dict[str, str]:
        rt = self.runtime
        reg = rt.registry
        comp = sections["baseline_comparison"]
        regr = sections["regression_watch"]
        return {
            "BASELINE_REGISTRY.md": self._baseline_registry_md(reg),
            "BASELINE_COMPARISON.md": self._kv_md(
                "Baseline Comparison", comp,
                ["overall", "improved_count", "regressed_count",
                 "safety_regressed", "empty_green_dashboard"]),
            "REGRESSION_WATCH.md": self._kv_md(
                "Regression Watch", regr,
                ["baseline_regression_count", "critical_regression_count",
                 "major_regression_count", "max_severity", "blocks_validation"]),
            "MODULE_STATUS_RECOMMENDATIONS.md": (
                f"# Module Status Recommendations\n\n"
                f"- update type: "
                f"{sections['module_status_recommendations'].get('update_type')}\n"
                f"- reasons: "
                f"{sections['module_status_recommendations'].get('reasons')}\n\n"
                "_Metadata only; no module or source is changed._\n"),
            "ROLLBACK_WATCH.md": (
                f"# Rollback Watch\n\n"
                f"- recommendation: "
                f"{sections['rollback_watch'].get('recommendation')}\n"
                f"- triggers: {sections['rollback_watch'].get('triggers')}\n\n"
                "_Recommendation only; rollback is never executed and failed "
                "artifacts are preserved._\n"),
            "FOLLOWUP_QUEUE.md": self._followup_md(sections["followup_queue"]),
        }

    @staticmethod
    def _baseline_registry_md(reg: Any) -> str:
        lines = ["# Baseline Registry", "",
                 "| baseline | parent | status | blocked |",
                 "| --- | --- | --- | --- |"]
        for bid, rec in reg.records.items():
            d = rec.to_dict()
            lines.append(f"| {bid} | {d['parent_baseline_id'] or '-'} | "
                         f"{d['status']} | {d['blocked']} |")
        lines += ["", "_Append-only; failed/blocked baselines remain visible "
                  "and are never deleted._"]
        return PostMergeAssimilationReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _followup_md(followup: Dict[str, Any]) -> str:
        lines = ["# Follow-Up Queue", ""]
        for item in followup.get("items", []):
            lines.append(f"- [{item['priority']}] {item['item_type']} "
                         f"({item['status']}) -- {item.get('detail', '')}")
        if not followup.get("items"):
            lines.append("- no follow-up items")
        lines += ["", "_Local metadata queue; it executes no task, calls no "
                  "external tool, and modifies no source._"]
        return PostMergeAssimilationReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _kv_md(title: str, data: Dict[str, Any], keys: List[str]) -> str:
        lines = [f"# {title}", ""]
        for k in keys:
            lines.append(f"- {k}: {data.get(k)}")
        lines += ["", "_Post-merge evidence assimilation only; no source/Git/"
                  "GitHub/merge action was taken._"]
        return PostMergeAssimilationReportBuilder._guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "POST_MERGE_ASSIMILATION_REPORT.md")
        json_path = os.path.join(base, "POST_MERGE_ASSIMILATION_REPORT.json")
        markdown = self._render_main(report["sections"])
        if not report["claim_guard_safe"]:
            markdown = self._guard(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        written = [md_path, json_path]
        for name, body in self._sub_reports(report["sections"]).items():
            path = os.path.join(base, name)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self._guard(body))
            written.append(path)
        return {"markdown": md_path, "json": json_path, "documents": written,
                "report": report}
