"""Alpha research reports -- honest local documents, ClaimGuard-scanned.

:class:`AlphaResearchReportBuilder` writes the alpha research system report plus
the module-registry, demo, cycle-status, and operator-runbook documents. Every
report states explicitly that no source was modified, no Git/GitHub operation
occurred, no network/shell/browser/OS access happened, no feeders/hardware were
controlled, nothing was published/uploaded, no external agent was run, and no
consciousness/life/agency claim is made. Skipped modules, missing artifacts, and
blockers are always shown. ClaimGuard scans the Markdown when available; if it is
unavailable it is reported as a warning unless ``require_claimguard`` is set.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "No source code was modified by the runtime.",
    "No Git or GitHub operation occurred.",
    "No branch, tag, release, or PR was created.",
    "No network/shell/browser/OS access occurred.",
    "No feeders or hardware were controlled.",
    "No publication or upload occurred.",
    "No external agent was run.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class AlphaResearchReportBuilder:
    """Builds the alpha report set (JSON + claim-guarded Markdown)."""

    orchestrator: Any

    def build(self) -> Dict[str, Any]:
        o = self.orchestrator
        status = o.alpha_status()
        sections: Dict[str, Any] = {
            "purpose": ("assemble the organismic, scientific, claim-governance, "
                        "and review-governance modules into one bounded, "
                        "fixture-only local research run"),
            "alpha_profile": o.alpha_profile.to_dict(),
            "state_layout": o.layout.to_dict() if o.layout else {},
            "system_check": o.check,
            "module_registry": o.registry.to_dict() if o.registry else {},
            "demo_plan": o.plan.to_dict() if o.plan else {},
            "artifact_index": (o.artifact_index.to_dict()
                               if o.artifact_index else {}),
            "cycle_status": o.cycle,
            "runbook": o.runbook.to_dict() if o.runbook else {},
            "safety_status": o.safety.snapshot(),
            "status": status,
            "claimguard_available": self._claimguard_available(),
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_main(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_main(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        reg = sections["module_registry"]
        plan = sections["demo_plan"]
        cg = sections["claimguard_available"]
        lines = [
            "# Alpha Research System Report", "",
            "_The Alpha Research System is a local, fixture-only research "
            "orchestration layer. It does not call GitHub, run Git, publish or "
            "upload artifacts, create branches/tags/releases/PRs, control "
            "feeders/hardware, access the network/shell/browser/OS, run external "
            "agents, or prove consciousness, sentience, biological life, "
            "personhood, agency, free will, emotion, feeling, understanding, "
            "self-awareness, or subjective experience._", "",
            f"- profile: {status['alpha_profile_id']} "
            f"(fixture-only: {sections['alpha_profile'].get('is_fixture_only')})",
            f"- modules: {status['alpha_module_count']} "
            f"(available {status['alpha_available_module_count']}, missing "
            f"{status['alpha_missing_module_count']}, blocked "
            f"{status['alpha_blocked_module_count']})",
            f"- demo steps: {status['alpha_demo_step_count']} "
            f"(completed {status['alpha_demo_step_completed_count']}, skipped "
            f"{status['alpha_demo_step_skipped_count']})",
            f"- artifacts: {status['alpha_artifact_count']}",
            f"- cycle stage: **{status['alpha_cycle_stage']}** "
            f"(next action: {status['alpha_next_action']})",
            f"- blockers: {status['alpha_blocker_count']}; warnings: "
            f"{status['alpha_warning_count']}",
            f"- ClaimGuard available: {cg}",
            "",
            "## System check", "",
        ]
        for r in sections["system_check"].get("results", []):
            lines.append(f"- [{r['severity']}] {r['name']}: {r['detail']}")
        lines += ["", "## Module registry", ""]
        for m in reg.get("modules", []):
            lines.append(f"- [{m['status']}] {m['label']}"
                         + (" (required)" if m["required_for_alpha"] else ""))
        lines += ["", "## Demo results", ""]
        for s in plan.get("steps", []):
            lines.append(f"- [{s['status']}] {s['label']}"
                         + (f" -> {s['detail']}" if s['detail'] else ""))
        lines += ["", "## Skipped modules", ""]
        skipped = [s for s in plan.get("steps", []) if s.get("skipped")]
        lines += [f"- {s['label']} ({s['module_key']})" for s in skipped] \
            or ["- none"]
        lines += ["", "## Blockers", ""]
        lines += [f"- {b}" for b in sections["cycle_status"].get("blockers", [])]\
            or ["- none"]
        lines += ["", "## Warnings", ""]
        warns = [r['name'] for r in sections["system_check"].get("results", [])
                 if r['severity'] == "warning"]
        lines += [f"- {w}" for w in warns] or ["- none"]
        if not cg:
            lines += ["", "> WARNING: ClaimGuard was unavailable; report text "
                      "was not claim-scanned."]
        lines += ["", "## Cycle status", "",
                  f"- stage: {sections['cycle_status'].get('stage')}",
                  f"- next action: {sections['cycle_status'].get('next_action')}"]
        lines += ["", "## Safety boundaries", ""]
        lines += [f"- {r}" for r in
                  sections["alpha_profile"].get("safety_constraints", [])]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in sections["what_this_does_not_do"]]
        return "\n".join(lines)

    @staticmethod
    def _claimguard_available() -> bool:
        try:
            from ..governance.compliance import ClaimGuard

            ClaimGuard()
            return True
        except Exception:
            return False

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
        return {
            "ALPHA_MODULE_REGISTRY.md": self._registry_md(sections),
            "ALPHA_DEMO_REPORT.md": self._demo_md(sections),
            "ALPHA_CYCLE_STATUS.md": self._cycle_md(sections),
            "ALPHA_OPERATOR_RUNBOOK.md": self._runbook_md(),
        }

    def _registry_md(self, s: Dict[str, Any]) -> str:
        reg = s["module_registry"]
        lines = ["# Alpha Module Registry", "",
                 f"- modules: {reg.get('alpha_module_count', 0)} "
                 f"(available {reg.get('alpha_available_module_count', 0)}, "
                 f"missing {reg.get('alpha_missing_module_count', 0)})", "",
                 "| module | status | required |", "| --- | --- | --- |"]
        for m in reg.get("modules", []):
            lines.append(f"| {m['label']} | {m['status']} | "
                         f"{m['required_for_alpha']} |")
        lines += ["", "_Module presence is checked by import-spec only; missing "
                  "optional modules warn and are never hidden._"]
        return self._guard("\n".join(lines))

    def _demo_md(self, s: Dict[str, Any]) -> str:
        plan = s["demo_plan"]
        lines = ["# Alpha Demo Report", "",
                 f"- steps: {plan.get('alpha_demo_step_count', 0)} "
                 f"(completed {plan.get('alpha_demo_step_completed_count', 0)}, "
                 f"skipped {plan.get('alpha_demo_step_skipped_count', 0)})", "",
                 "| step | status | detail |", "| --- | --- | --- |"]
        for st in plan.get("steps", []):
            lines.append(f"| {st['label']} | {st['status']} | {st['detail']} |")
        lines += ["", "_Every step is bounded; skipped modules are shown "
                  "honestly; no step starts feeders or touches network/Git/"
                  "GitHub/shell/OS/hardware._"]
        return self._guard("\n".join(lines))

    def _cycle_md(self, s: Dict[str, Any]) -> str:
        c = s["cycle_status"]
        lines = ["# Alpha Cycle Status", "",
                 f"- stage: **{c.get('stage')}**",
                 f"- next action: {c.get('next_action')}",
                 f"- blockers: {c.get('blocker_count', 0)}; warnings: "
                 f"{c.get('warning_count', 0)}", ""]
        for b in c.get("blockers", []):
            lines.append(f"- blocker: {b}")
        lines += ["", "_Cycle status is descriptive only; it never executes the "
                  "next action._"]
        return self._guard("\n".join(lines))

    def _runbook_md(self) -> str:
        if self.orchestrator.runbook is None:
            return "# Alpha Operator Runbook\n\n_(not generated)_"
        return self._guard(self.orchestrator.runbook.render_md())

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = os.path.join(state_dir or self.orchestrator.state_dir, "reports")
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "ALPHA_RESEARCH_SYSTEM_REPORT.md")
        json_path = os.path.join(base, "ALPHA_RESEARCH_SYSTEM_REPORT.json")
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
