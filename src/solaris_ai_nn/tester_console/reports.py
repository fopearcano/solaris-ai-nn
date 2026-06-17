"""Tester console report set -- the console's own report + status JSON.

:class:`TesterConsoleReportBuilder` writes the console report (Markdown + JSON), the
console status JSON, and the artifact-discovery / safety-panel / next-action sub-reports.
Every report states that the console is read-only and controls nothing. ClaimGuard scans
the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict

_WHAT_THIS_DOES_NOT_DO = (
    "This console is read-only.",
    "It does not start, stop, schedule, or control feeders.",
    "It does not control hardware.",
    "It does not access network/Git/GitHub/shell/browser/OS.",
    "It does not run a server or open a browser.",
    "It does not publish or upload anything.",
    "It does not execute artifact contents.",
    "It does not treat tester notes as training.",
    "It does not make consciousness/life/agency claims.",
)


@dataclass
class TesterConsoleReportBuilder:
    """Builds the console report set (Markdown + JSON)."""

    runtime: Any

    def write(self) -> Dict[str, Any]:
        rt = self.runtime
        os.makedirs(rt.console_dir, exist_ok=True)
        reports_dir = os.path.join(rt.console_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        summary = rt._run_summary()

        md = _guard(self._report_md(summary))
        md_path = os.path.join(rt.console_dir, "CONSOLE_REPORT.md")
        _w(md_path, md)
        _wj(os.path.join(rt.console_dir, "CONSOLE_REPORT.json"),
            {"sections": summary, "claim_guard_safe": _safe(md)})
        _wj(os.path.join(rt.console_dir, "CONSOLE_STATUS.json"),
            rt.console_status())

        _w(os.path.join(reports_dir, "CONSOLE_ARTIFACT_DISCOVERY.md"),
           _guard(self._discovery_md(summary)))
        _w(os.path.join(reports_dir, "CONSOLE_SAFETY_PANEL.md"),
           _guard(self._safety_md(summary)))
        _w(os.path.join(reports_dir, "CONSOLE_NEXT_ACTIONS.md"),
           _guard(self._next_actions_md(summary)))
        return {"markdown": md_path,
                "json": os.path.join(rt.console_dir, "CONSOLE_REPORT.json"),
                "status": os.path.join(rt.console_dir, "CONSOLE_STATUS.json")}

    def _report_md(self, s: Dict[str, Any]) -> str:
        st = s["console_status"]
        lines = ["# Tester Console Report", "",
                 "_This console is read-only and controls nothing._", "",
                 "## Purpose", "",
                 self.runtime.console_profile.purpose, "",
                 "## Profile", "",
                 f"- {st['console_profile']} (read-only: {st['read_only']}, "
                 f"server: {st['runs_server']}, browser: {st['opens_browser']})",
                 "", "## Artifact discovery summary", "",
                 f"- artifacts discovered: {st['artifact_count']}",
                 f"- missing required artifacts: {st['missing_artifact_count']}",
                 "", "## Status summary", "",
                 f"- overall health: **{st['overall_health']}**",
                 f"- release ready: {st['release_ready']}",
                 f"- blockers: {st['blocker_count']}; warnings: "
                 f"{st['warning_count']}", "",
                 "## Safety panel", "",
                 f"- safety status: **{st['safety_status']}** "
                 f"(blockers {st['safety_block_count']})", "",
                 "## Run index", "",
                 f"- runs: {st['run_index_count']}", "",
                 "## Dashboard files generated", ""]
        for kind, val in s["generated_files"].items():
            lines.append(f"- {kind}: {val}")
        lines += ["", "## Next actions", ""]
        for a in s["next_actions"]["actions"]:
            lines.append(f"- [{a['priority']}] {a['action']} -- {a['detail']}")
        lines += ["", "## Limitations", ""]
        lines += [f"- {l}" for l in self.runtime.console_profile.limitations]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in _WHAT_THIS_DOES_NOT_DO]
        return "\n".join(lines)

    def _discovery_md(self, s: Dict[str, Any]) -> str:
        d = s["discovery"]
        lines = ["# Console Artifact Discovery", "",
                 "_Read-only discovery; raw private payloads are not shown._", "",
                 f"- artifacts: {d.get('artifact_count', 0)}",
                 f"- by kind: {d.get('by_kind', {})}", "",
                 "## Roots scanned", ""]
        for root, present in d.get("roots_scanned", {}).items():
            lines.append(f"- {root}: {'present' if present else 'absent'}")
        return "\n".join(lines)

    def _safety_md(self, s: Dict[str, Any]) -> str:
        sp = s["safety_panel"]
        lines = ["# Console Safety Panel", "",
                 f"- status: **{sp.get('safety_status')}** "
                 f"(blockers {sp.get('blocker_count', 0)})", "",
                 "| check | severity | detail |", "| --- | --- | --- |"]
        for f in sp.get("findings", []):
            lines.append(f"| {f['check']} | {f['severity']} | {f['detail']} |")
        lines += ["", "_Safety findings are never buried below optional "
                  "summaries._"]
        return "\n".join(lines)

    def _next_actions_md(self, s: Dict[str, Any]) -> str:
        na = s["next_actions"]
        lines = ["# Console Next Actions", "",
                 "_Recommendations only; the console never executes them._", "",
                 f"- top action: {na.get('top_action')}", "",
                 "| priority | action | detail | manual approval |",
                 "| --- | --- | --- | --- |"]
        for a in na.get("actions", []):
            lines.append(f"| {a['priority']} | {a['action']} | {a['detail']} | "
                         f"{'yes' if a['requires_manual_approval'] else ''} |")
        return "\n".join(lines)


def _w(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _wj(path: str, obj: Any) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, default=str)


def _safe(text: str) -> bool:
    try:
        from ..governance.compliance import ClaimGuard
        return ClaimGuard().scan_text(text).safe
    except Exception:
        return True


def _guard(text: str) -> str:
    try:
        from ..governance.compliance import ClaimGuard
        guard = ClaimGuard()
        if not guard.scan_text(text).safe:
            return guard.rewrite(text)
    except Exception:
        pass
    return text
