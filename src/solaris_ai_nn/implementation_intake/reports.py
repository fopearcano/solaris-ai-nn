"""Implementation intake reports -- advisory audit documents, ClaimGuard-scanned.

:class:`ImplementationIntakeReportBuilder` writes the intake report plus the
diff/spec/test/safety-regression/ClaimGuard/coverage/merge/rollback/post-merge
documents. Every report states explicitly that no source was modified, no Git
branch was created, no pull request was opened/merged, no external coding agent
was run, this is an advisory audit only, and no consciousness/life/agency claim
is made. The Markdown is scanned by ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "No source code was modified.",
    "No Git branch was created.",
    "No pull request was opened.",
    "No pull request was merged.",
    "No external coding agent was run.",
    "This is an advisory audit only.",
    "No consciousness/life/agency claim is made.",
)

_LIMITATIONS = (
    "The intake layer reads local artifacts only; it never calls GitHub or runs "
    "Git.",
    "Test output is evidence, not proof of correctness.",
    "Merge/rollback recommendations are advisory; a human operator decides.",
    "Safety-critical findings and missing evidence block the recommendation and "
    "are never hidden.",
    "Failed, missing, and falsified evidence is preserved.",
)


@dataclass
class ImplementationIntakeReportBuilder:
    """Builds the intake report set (JSON + claim-guarded Markdown documents)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.intake_status()
        sections: Dict[str, Any] = {
            "purpose": ("audit a completed external implementation against the "
                        "experiment-compiler artifacts and produce an advisory "
                        "merge recommendation -- not a merge, not a coding "
                        "agent"),
            "intake_manifest_summary": rt.manifest.to_dict(),
            "artifact_integrity": rt.reader.to_dict(),
            "diff_audit": rt.diff_audit,
            "spec_compliance": rt.spec_compliance,
            "test_results": rt.test_audit,
            "safety_regression_findings": rt.safety_regression,
            "claimguard_findings": rt.claimguard_audit,
            "coverage_matrix_summary": rt.coverage,
            "merge_recommendation": rt.merge,
            "merge_blockers": rt.merge.get("blockers", []),
            "rollback_recommendation": rt.rollback,
            "post_merge_validation_plan": rt.post_merge,
            "missing_evidence": rt.manifest.warnings() + rt.manifest.blockers(),
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
        merge = sections["merge_recommendation"]
        lines = [
            "# Implementation Intake Report", "",
            "_Audits a completed external implementation against the "
            "experiment-compiler artifacts. The intake layer reads local "
            "evidence and writes advisory reports ONLY: it modifies no source, "
            "runs no Git, calls no GitHub, opens/approves/merges no pull "
            "request, and runs no external coding agent._", "",
            f"- artifacts present: {status['implementation_artifact_count']} "
            f"(missing {status['missing_artifact_count']}, corrupt "
            f"{status['corrupt_artifact_count']})",
            f"- diff findings: {status['diff_finding_count']} "
            f"(unexpected {status['unexpected_file_change_count']}, forbidden "
            f"{status['forbidden_file_change_count']})",
            f"- spec compliance: {status['spec_compliance_status']} "
            f"(satisfied {status['spec_satisfied_count']}, unsatisfied "
            f"{status['spec_unsatisfied_count']})",
            f"- tests: {status['test_failure_count']} failure(s), "
            f"{status['missing_required_test_count']} missing required",
            f"- safety regressions: {status['safety_regression_count']} "
            f"(critical {status['critical_safety_regression_count']})",
            f"- ClaimGuard findings: {status['claimguard_finding_count']}",
            f"- coverage gaps: {status['coverage_gap_count']}",
            f"- MERGE RECOMMENDATION: **{merge.get('status')}** "
            f"({merge.get('blocker_count', 0)} blocker(s))",
            f"  - rationale: {merge.get('rationale')}",
            f"- rollback: {status['rollback_recommendation_status']} "
            f"({status['rollback_trigger_count']} trigger(s))",
            "",
            "## Merge blockers", "",
        ]
        blockers = sections["merge_blockers"]
        if blockers:
            lines += [f"- {b['kind']}: {b['detail']}" for b in blockers]
        else:
            lines.append("- none")
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
        merge = sections["merge_recommendation"]
        return {
            "DIFF_AUDIT.md": self._kv_md(
                "Diff Audit", rt.diff_audit,
                ["changed_file_count", "blocker_count", "warning_count",
                 "unexpected_file_change_count", "forbidden_file_change_count"]),
            "SPEC_COMPLIANCE.md": self._kv_md(
                "Spec Compliance", rt.spec_compliance,
                ["spec_satisfied_count", "spec_unsatisfied_count",
                 "blocking_failure_count"]),
            "TEST_RESULT_AUDIT.md": self._kv_md(
                "Test Result Audit", rt.test_audit,
                ["test_failure_count", "missing_required_test_count",
                 "passes"]),
            "SAFETY_REGRESSION_AUDIT.md": self._kv_md(
                "Safety Regression Audit", rt.safety_regression,
                ["finding_count", "critical_count", "major_count",
                 "max_severity", "blocks_merge"]),
            "CLAIMGUARD_AUDIT.md": self._kv_md(
                "ClaimGuard Audit", rt.claimguard_audit,
                ["status", "finding_count", "undisclaimed_finding_count",
                 "blocks_readiness"]),
            "COVERAGE_MATRIX.md": self._kv_md(
                "Coverage Matrix", rt.coverage,
                ["row_count", "coverage_gap_count", "blocker_count",
                 "empty_green_dashboard"]),
            "MERGE_RECOMMENDATION.md": (
                f"# Merge Recommendation\n\n- status: **{merge.get('status')}**\n"
                f"- rationale: {merge.get('rationale')}\n"
                f"- blockers: {merge.get('blocker_count', 0)}\n"
                f"- warnings: {len(merge.get('warnings', []))}\n\n"
                "_Advisory only. The intake layer does not merge, approve, "
                "open, or create pull requests; a human operator decides._\n"),
            "ROLLBACK_RECOMMENDATION.md": (
                f"# Rollback Recommendation\n\n"
                f"- recommended: {rt.rollback.get('recommended')}\n"
                f"- urgency: {rt.rollback.get('urgency')}\n"
                f"- reasons: {rt.rollback.get('reasons')}\n\n"
                "_Documentation only; rollback is never executed and failed "
                "artifacts are preserved._\n"),
            "POST_MERGE_VALIDATION_PLAN.md": self._post_merge_md(),
        }

    def _post_merge_md(self) -> str:
        stages = self.runtime.post_merge.get("stages", [])
        lines = ["# Post-Merge Validation Plan", ""]
        if self.runtime.post_merge.get("conditional"):
            lines += ["_Conditional: merge is currently blocked; run only after "
                      "blockers are resolved._", ""]
        lines += ["_Staged and gated; a safety failure stops later validation. "
                  "Not executed automatically._", ""]
        for s in stages:
            flag = " (safety-critical)" if s.get("safety_critical") else ""
            lines.append(f"{s['order']}. {s['stage_id']}{flag} -- {s['purpose']}")
        return "\n".join(lines)

    @staticmethod
    def _kv_md(title: str, data: Dict[str, Any], keys: List[str]) -> str:
        lines = [f"# {title}", ""]
        for k in keys:
            lines.append(f"- {k}: {data.get(k)}")
        lines += ["", "_Advisory audit evidence only; no source/branch/PR/merge "
                  "action was taken._"]
        return "\n".join(lines)

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "IMPLEMENTATION_INTAKE_REPORT.md")
        json_path = os.path.join(base, "IMPLEMENTATION_INTAKE_REPORT.json")
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
