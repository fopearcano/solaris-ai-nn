"""Research cycle reports -- local cycle-tracking documents, ClaimGuard-scanned.

:class:`ResearchCycleReportBuilder` writes the research cycle report plus the
cycle-state / evidence-ledger / artifact-graph / decision-gates / operator-
decisions / blocked-states / next-actions / archive documents. Every report
states explicitly that this is research-cycle tracking only -- no source change,
no Git command, no GitHub call, no branch/tag/release/PR, no validation execution,
no external agent -- and makes no consciousness/life/agency claim. ClaimGuard
scans the Markdown.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "This is research-cycle tracking only.",
    "No source code was modified.",
    "No Git command was run.",
    "No GitHub call was made.",
    "No branch, tag, release, or PR was created.",
    "No validation command was executed automatically.",
    "No external coding agent was run.",
    "No consciousness/life/agency claim is made.",
)

_LIMITATIONS = (
    "The cycle tracker reads local artifacts and writes reports only.",
    "Operator decision gates cannot be auto-approved; the system cannot approve "
    "itself.",
    "A critical safety blocker can never be bypassed.",
    "Missing, negative, and falsified evidence is preserved, never deleted.",
    "Next actions are recommendations for the operator; none is executed.",
)


@dataclass
class ResearchCycleReportBuilder:
    """Builds the research cycle report set (JSON + claim-guarded Markdown)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.research_cycle_status()
        sections: Dict[str, Any] = {
            "purpose": ("track where the Solaris-AI-NN research program is in "
                        "its experimental cycle, what evidence supports the "
                        "current state, what is blocked, and what the operator "
                        "should do next -- tracking only, not execution"),
            "current_cycle_id": status["current_cycle_id"],
            "parent_cycle_id": status["parent_cycle_id"],
            "current_baseline": status["current_baseline_id"],
            "cycle_manifest": rt.manifest.to_dict() if rt.manifest else {},
            "cycle_state": rt.state,
            "evidence_ledger": rt.ledger.to_dict(),
            "artifact_graph": rt.graph,
            "decision_gates": rt.gates,
            "operator_decision_requirements": rt.operator_required,
            "blocked_states": rt.blocked,
            "cycle_transitions": rt.transitions,
            "next_actions": rt.next_actions,
            "cycle_archive": rt.archive.to_dict(),
            "missing_evidence": rt.state.get("missing_evidence", []),
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
            "# Research Cycle Report", "",
            "_Tracks where the research program is in its experimental cycle "
            "(baseline -> proposal -> experiment pack -> implementation intake "
            "-> post-merge assimilation -> research baseline -> soak/"
            "replication). This is tracking ONLY: it modifies no source, runs "
            "no Git, calls no GitHub, creates no branch/tag/release/PR, executes "
            "no validation command, and runs no external agent._", "",
            f"- cycle: {status['current_cycle_id']} "
            f"(parent {status['parent_cycle_id'] or 'none'})",
            f"- baseline: {status['current_baseline_id'] or 'none'}",
            f"- stage: **{status['current_cycle_stage']}** "
            f"({status['current_cycle_status']})",
            f"- decision gates: {status['decision_gate_count']} "
            f"(failed {status['failed_decision_gate_count']})",
            f"- operator decisions required: "
            f"{status['operator_decision_required_count']}",
            f"- blocked states: {status['blocked_state_count']} "
            f"(unresolved {status['unresolved_blocker_count']})",
            f"- evidence ledger entries: "
            f"{status['evidence_ledger_entry_count']} "
            f"(missing {status['missing_evidence_entry_count']}, negative "
            f"{status['negative_evidence_entry_count']}, falsified "
            f"{status['falsified_evidence_entry_count']})",
            f"- artifact graph: {status['artifact_graph_node_count']} node(s), "
            f"{status['artifact_graph_contradiction_count']} contradiction(s)",
            f"- next actions: {status['next_action_count']}",
            "",
            "## Next actions (for the operator)", "",
        ]
        for a in sections["next_actions"].get("actions", []):
            ctx = f" [{a['safety_context']}]" if a.get("safety_context") else ""
            lines.append(f"- [{a['priority']}] {a['action_type']}: "
                         f"{a['detail']}{ctx}")
        lines += ["", "## Blocked states", ""]
        states = sections["blocked_states"].get("states", [])
        lines += [f"- {s['reason']} -> {s['recommendation']}"
                  + (" (critical safety; cannot bypass)"
                     if s.get("critical_safety") else "")
                  for s in states] or ["- none"]
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
        s = sections
        return {
            "CYCLE_STATE.md": self._kv_md(
                "Cycle State", s["cycle_state"],
                ["stage", "status", "blocked", "missing_evidence"]),
            "EVIDENCE_LEDGER.md": self._kv_md(
                "Evidence Ledger", s["evidence_ledger"],
                ["evidence_ledger_entry_count", "missing_evidence_entry_count",
                 "negative_evidence_entry_count", "falsified_evidence_entry_count",
                 "superseded_count", "append_only"]),
            "ARTIFACT_GRAPH.md": self._graph_md(s),
            "DECISION_GATES.md": self._gates_md(s),
            "OPERATOR_DECISIONS.md": self._operator_md(s),
            "BLOCKED_STATES.md": self._blocked_md(s),
            "NEXT_ACTIONS.md": self._next_md(s),
            "CYCLE_ARCHIVE.md": self._kv_md(
                "Cycle Archive", s["cycle_archive"], ["archived_cycle_count"]),
        }

    @staticmethod
    def _kv_md(title: str, data: Dict[str, Any], keys: List[str]) -> str:
        lines = [f"# {title}", ""]
        for k in keys:
            lines.append(f"- {k}: {data.get(k)}")
        lines += ["", "_Research-cycle tracking only; no source/Git/GitHub/"
                  "validation action was taken._"]
        return ResearchCycleReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _graph_md(s: Dict[str, Any]) -> str:
        g = s["artifact_graph"]
        lines = ["# Artifact Graph", "",
                 f"- nodes: {g.get('artifact_graph_node_count', 0)} "
                 f"(missing {len(g.get('missing_nodes', []))})",
                 f"- contradictions: "
                 f"{g.get('artifact_graph_contradiction_count', 0)}", "",
                 "| src | edge | dst |", "| --- | --- | --- |"]
        for e in g.get("edges", []):
            lines.append(f"| {e['src']} | {e['edge_type']} | {e['dst']} |")
        lines += ["", "_Evidence provenance, not cognition; contradictions and "
                  "missing nodes stay visible._"]
        return ResearchCycleReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _gates_md(s: Dict[str, Any]) -> str:
        g = s["decision_gates"]
        lines = ["# Decision Gates", "",
                 f"- gates: {g.get('decision_gate_count', 0)} "
                 f"(failed {g.get('failed_decision_gate_count', 0)}, waiting "
                 f"{g.get('waiting_for_operator_count', 0)})", "",
                 "| gate | status |", "| --- | --- |"]
        for r in g.get("results", []):
            lines.append(f"| {r['gate_type']} | {r['status']} |")
        lines += ["", "_Gate results are advisory; operator gates cannot be "
                  "auto-approved._"]
        return ResearchCycleReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _operator_md(s: Dict[str, Any]) -> str:
        lines = ["# Operator Decisions Required", ""]
        reqs = s["operator_decision_requirements"]
        lines += [f"- {r['decision_type']}: {r['detail']}" for r in reqs] or [
            "- none"]
        lines += ["", "_Operator decisions are explicit local artifacts; the "
                  "system cannot invent or auto-approve them._"]
        return ResearchCycleReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _blocked_md(s: Dict[str, Any]) -> str:
        b = s["blocked_states"]
        lines = ["# Blocked States", "",
                 f"- blocked states: {b.get('blocked_state_count', 0)} "
                 f"(critical safety {b.get('critical_safety_blocker_count', 0)})",
                 ""]
        for st in b.get("states", []):
            lines.append(f"- {st['reason']} -> {st['recommendation']}"
                         + (" (critical safety; cannot bypass)"
                            if st.get("critical_safety") else ""))
        lines += ["", "_The resolver recommends only; a critical safety blocker "
                  "can never be bypassed._"]
        return ResearchCycleReportBuilder._guard("\n".join(lines))

    @staticmethod
    def _next_md(s: Dict[str, Any]) -> str:
        lines = ["# Next Actions", ""]
        for a in s["next_actions"].get("actions", []):
            lines.append(f"- [{a['priority']}] {a['action_type']}: "
                         f"{a['detail']}")
        lines += ["", "_Next actions are instructions for the operator; none is "
                  "executed automatically._"]
        return ResearchCycleReportBuilder._guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = state_dir or self.runtime.state_dir
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "RESEARCH_CYCLE_REPORT.md")
        json_path = os.path.join(base, "RESEARCH_CYCLE_REPORT.json")
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
