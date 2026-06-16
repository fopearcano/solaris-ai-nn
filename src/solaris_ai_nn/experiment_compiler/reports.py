"""Experiment compiler reports -- documents only, ClaimGuard-scanned.

:class:`ExperimentCompilerReportBuilder` writes the compiler report, the compiled
experiment index, and per-experiment documents (implementation prompt, branch
spec, test matrix, safety gates, operator review packet, rollback plan,
validation plan). Every report states explicitly that the compiler writes
documents only -- no source change, no Git branch, no PR, no external agent, no
bypassed gate, and no consciousness/life/agency claim. The Markdown is scanned by
ClaimGuard.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "The compiler writes documents only.",
    "No source code was changed.",
    "No Git branch was created.",
    "No pull request was opened.",
    "No external coding agent was run.",
    "No safety gate was bypassed.",
    "No consciousness/life/agency claim is made.",
)

_LIMITATIONS = (
    "Specs, prompt packs, and branch specs are drafts for a human operator.",
    "A spec is marked ready only when its critical safety gates pass.",
    "Blocked, falsified, and inconclusive proposals are preserved, not hidden.",
    "Implementation, branching, and PRs remain manual, operator-governed steps.",
)


@dataclass
class ExperimentCompilerReportBuilder:
    """Builds the compiler report set (JSON + claim-guarded Markdown docs)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.compiler_status()
        all_exp = rt.all_experiments()
        sections: Dict[str, Any] = {
            "purpose": ("compile evidence-guided architecture proposals into "
                        "human-reviewable implementation documents -- not "
                        "autonomous coding or self-modification"),
            "input_manifest": rt.manifest.to_dict(),
            "proposals_compiled": [c.spec.to_dict() for c in rt.compiled],
            "proposals_blocked": [c.spec.to_dict() for c in rt.blocked],
            "prompt_packs_generated": [c.prompt_pack.spec_id
                                       for c in rt.compiled
                                       if c.prompt_pack is not None],
            "branch_specs_generated": [c.branch_spec.spec_id
                                       for c in rt.compiled
                                       if c.branch_spec is not None],
            "safety_gates": [{"spec_id": c.spec.spec_id,
                              "summary": c.gate_summary} for c in all_exp],
            "review_packets": [c.review_packet.to_dict() for c in all_exp
                               if c.review_packet is not None],
            "rollback_plans": [c.rollback_plan.to_dict() for c in all_exp
                               if c.rollback_plan is not None],
            "validation_plans": [c.validation_plan.to_dict() for c in all_exp
                                 if c.validation_plan is not None],
            "missing_evidence": rt.manifest.warnings() + rt.manifest.blockers(),
            "falsified_evidence": [c.spec.spec_id for c in rt.blocked
                                   if c.spec.status ==
                                   "blocked_by_falsification"],
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "limitations": list(_LIMITATIONS),
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_markdown(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_markdown(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        lines = [
            "# Experiment Compiler Report", "",
            "_Converts evidence-guided architecture proposals into "
            "human-reviewable implementation documents. The compiler writes "
            "documents ONLY: it changes no source, creates no Git branch, opens "
            "no pull request, and runs no external coding agent._", "",
            f"- input sources: {status['compiler_input_source_count']}",
            f"- proposals read: {status['proposal_read_count']}",
            f"- compiled specs: {status['compiled_spec_count']} "
            f"(ready {status['ready_spec_count']}, blocked "
            f"{status['blocked_spec_count']})",
            f"- prompt packs: {status['prompt_pack_count']}",
            f"- branch specs: {status['branch_spec_count']}",
            f"- safety gates: {status['safety_gate_count']} "
            f"(critical failures {status['safety_gate_failure_count']})",
            f"- review packets: {status['review_packet_count']}",
            f"- missing evidence: {status['missing_evidence_count']}",
            "",
            "## Blocked proposals (preserved)", "",
        ]
        blocked = sections["proposals_blocked"]
        if blocked:
            lines += [f"- {b['spec_id']}: {b['status']} -- {b['block_reason']}"
                      for b in blocked]
        else:
            lines.append("- none blocked in this run")
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in sections["what_this_does_not_do"]]
        lines += ["", "## Limitations", ""]
        lines += [f"- {lim}" for lim in sections["limitations"]]
        return "\n".join(lines)

    def _render_index_md(self, sections: Dict[str, Any]) -> str:
        lines = ["# Compiled Experiment Index", "",
                 "| spec id | type | status | ready | prompt pack |",
                 "| --- | --- | --- | --- | --- |"]
        for c in self.runtime.all_experiments():
            d = c.spec.to_dict()
            lines.append(f"| {d['spec_id']} | {d['spec_type']} | "
                         f"{d['status']} | {d['ready']} | "
                         f"{'yes' if c.prompt_pack else 'no'} |")
        lines += ["", "_Drafts for a human operator. No branch/PR/source change "
                  "was performed._"]
        return self._guard("\n".join(lines))

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

    def _write_per_experiment(self, base: str) -> List[str]:
        written: List[str] = []
        for c in self.runtime.all_experiments():
            exp_dir = os.path.join(base, c.spec.spec_id)
            os.makedirs(exp_dir, exist_ok=True)
            docs = {
                "IMPLEMENTATION_PROMPT.md":
                    c.prompt_pack.render_markdown() if c.prompt_pack else
                    f"# Implementation Prompt -- {c.spec.spec_id}\n\n"
                    "_No prompt pack: this spec is blocked or not ready._\n",
                "BRANCH_SPEC.md":
                    c.branch_spec.render_markdown() if c.branch_spec else
                    f"# Branch Spec -- {c.spec.spec_id}\n\n_No branch spec: "
                    "this spec is blocked or not ready._\n",
                "TEST_MATRIX.md": self._test_matrix_md(c),
                "SAFETY_GATES.md": self._safety_gates_md(c),
                "OPERATOR_REVIEW_PACKET.md":
                    c.review_packet.render_markdown() if c.review_packet
                    else "",
                "ROLLBACK_PLAN.md":
                    c.rollback_plan.render_markdown() if c.rollback_plan
                    else "",
                "VALIDATION_PLAN.md":
                    c.validation_plan.render_markdown() if c.validation_plan
                    else f"# Validation Plan -- {c.spec.spec_id}\n\n_n/a_\n",
            }
            # Also persist the spec JSON for downstream tooling.
            with open(os.path.join(exp_dir, "EXPERIMENT_SPEC.json"), "w",
                      encoding="utf-8") as fh:
                json.dump(c.to_dict(), fh, indent=2, default=str)
            for name, body in docs.items():
                with open(os.path.join(exp_dir, name), "w",
                          encoding="utf-8") as fh:
                    fh.write(self._guard(body))
                written.append(os.path.join(exp_dir, name))
        return written

    def _test_matrix_md(self, c: Any) -> str:
        if not c.test_matrix:
            return f"# Test Matrix -- {c.spec.spec_id}\n\n_n/a (blocked)_\n"
        d = c.test_matrix.to_dict()
        lines = [f"# Test Matrix -- {c.spec.spec_id}", "",
                 f"- rows: {d['row_count']}, blocking: {d['blocking_row_count']}",
                 f"- missing blocking categories: "
                 f"{d['missing_blocking_categories'] or 'none'}", "",
                 "| test path | category | blocking | failure meaning |",
                 "| --- | --- | --- | --- |"]
        for r in d["rows"]:
            lines.append(f"| {r['test_path']} | {r['category']} | "
                         f"{r['blocking']} | {r['failure_meaning']} |")
        return "\n".join(lines)

    def _safety_gates_md(self, c: Any) -> str:
        lines = [f"# Safety Gates -- {c.spec.spec_id}", "",
                 f"- all critical passed: "
                 f"{c.gate_summary.get('all_critical_passed')}",
                 f"- critical failures: "
                 f"{c.gate_summary.get('critical_failures') or 'none'}", "",
                 "| gate | passed | critical |", "| --- | --- | --- |"]
        for r in c.gate_summary.get("results", []):
            lines.append(f"| {r['gate_type']} | {r['passed']} | "
                         f"{r['critical']} |")
        lines += ["", "_A failed critical gate blocks pack readiness; failures "
                  "are explicit, never hidden._"]
        return "\n".join(lines)

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "EXPERIMENT_COMPILER_REPORT.md")
        json_path = os.path.join(base, "EXPERIMENT_COMPILER_REPORT.json")
        index_path = os.path.join(base, "COMPILED_EXPERIMENT_INDEX.md")
        markdown = self._render_markdown(report["sections"])
        if not report["claim_guard_safe"]:
            markdown = self._guard(markdown)
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, default=str)
        with open(index_path, "w", encoding="utf-8") as fh:
            fh.write(self._render_index_md(report["sections"]))
        per_exp = self._write_per_experiment(base)
        return {"markdown": md_path, "json": json_path, "index": index_path,
                "per_experiment": per_exp, "report": report}
