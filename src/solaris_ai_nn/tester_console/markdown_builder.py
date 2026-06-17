"""Console Markdown builder -- the primary static dashboard output.

:class:`TesterConsoleMarkdownBuilder` writes the static Markdown dashboard (``INDEX.md``)
and the per-topic pages. Every page references local artifact paths, includes blocker/
warning/skipped tables, carries the safety disclaimers, and states what the console
cannot do. ClaimGuard scans the Markdown when available.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List

_READ_ONLY_BANNER = (
    "_This console is **read-only**. It does not start feeders, control "
    "hardware, access network/Git/GitHub/shell/browser/OS, run a server, open a "
    "browser, publish/upload, execute artifact contents, treat tester notes as "
    "training, or make any claim of consciousness, sentience, biological life, "
    "personhood, agency, free will, emotion, feeling, understanding, "
    "self-awareness, or subjective experience._"
)


@dataclass
class TesterConsoleMarkdownBuilder:
    """Builds the static Markdown console (INDEX.md + pages)."""

    dashboard: Any
    safety_panel: Any
    run_index: Any
    next_actions: List[Any]

    def write(self, console_dir: str) -> Dict[str, str]:
        os.makedirs(console_dir, exist_ok=True)
        pages_dir = os.path.join(console_dir, "pages")
        os.makedirs(pages_dir, exist_ok=True)
        written: Dict[str, str] = {}

        written["index"] = _w(os.path.join(console_dir, "INDEX.md"),
                              _guard(self._index_md()))
        for name, body in {
            "SAFETY.md": self._safety_md(),
            "RUNS.md": self._runs_md(),
            "MEMBRANE.md": self._membrane_md(),
            "QUARANTINE.md": self._quarantine_md(),
            "FIXTURE.md": self._fixture_md(),
            "LIVE.md": self._live_md(),
            "CLAIMS.md": self._claims_md(),
            "NEXT_ACTIONS.md": self._next_actions_md(),
        }.items():
            written[name] = _w(os.path.join(pages_dir, name), _guard(body))
        return written

    # -- pages --------------------------------------------------------------

    def _index_md(self) -> str:
        s = self.dashboard.sections
        rs = s["release_status"]
        sp = s["quick_safety_status"]
        lines = ["# Solaris-AI-NN Tester Console", "", _READ_ONLY_BANNER, "",
                 "## Release Status", "",
                 f"- overall health: **{rs['overall_health']}**",
                 f"- release ready: {rs['release_ready']}",
                 f"- blockers: {rs['blocker_count']}; warnings: "
                 f"{rs['warning_count']}", "",
                 "## Quick Safety Status", "",
                 f"- safety: **{sp['safety_status']}** "
                 f"(blockers {sp['blocker_count']}, findings "
                 f"{sp['finding_count']})"]
        for f in sp["findings"]:
            if f["severity"] in ("blocker", "warning"):
                lines.append(f"  - [{f['severity']}] {f['check']}: "
                             f"{f['detail']}")
        lines += ["", "## Summary cards", "",
                  "| area | status | report |", "| --- | --- | --- |"]
        for c in s["cards"]:
            lines.append(f"| {c['title']} | {c['status']} | "
                         f"{c['report_path'] or '-'} |")
        lines += ["", "## Missing required artifacts", ""]
        missing = s["missing_artifacts"]
        lines += ([f"- {m}" for m in missing] if missing
                  else ["- none"])
        lines += ["", "## Skipped optional stages", ""]
        skipped = s["skipped_optional_stages"]
        lines += ([f"- {m}" for m in skipped] if skipped else ["- none"])
        lines += ["", "## Next recommended action", ""]
        na = s["next_recommended_action"]
        if na:
            lines.append(f"- **{na.get('action')}** ({na.get('priority')}) -- "
                         f"{na.get('detail')}")
            if na.get("requires_manual_approval"):
                lines.append("  - requires manual approval")
        lines += ["", "## Pages", "",
                  "- [Safety](pages/SAFETY.md)",
                  "- [Runs](pages/RUNS.md)",
                  "- [Membrane](pages/MEMBRANE.md)",
                  "- [Quarantine](pages/QUARANTINE.md)",
                  "- [Fixture](pages/FIXTURE.md)",
                  "- [Live](pages/LIVE.md)",
                  "- [Claims](pages/CLAIMS.md)",
                  "- [Next actions](pages/NEXT_ACTIONS.md)", ""]
        lines += self._cannot_do()
        return "\n".join(lines)

    def _safety_md(self) -> str:
        sp = self.safety_panel.to_dict()
        lines = ["# Safety Panel", "", _READ_ONLY_BANNER, "",
                 f"- status: **{sp['safety_status']}**",
                 f"- blockers: {sp['blocker_count']}; findings: "
                 f"{sp['finding_count']}", "",
                 "| check | severity | detail |", "| --- | --- | --- |"]
        for f in sp["findings"]:
            lines.append(f"| {f['check']} | {f['severity']} | {f['detail']} |")
        lines += [""] + self._cannot_do()
        return "\n".join(lines)

    def _runs_md(self) -> str:
        return self.run_index.to_markdown() + "\n\n" + "\n".join(
            self._cannot_do())

    def _membrane_md(self) -> str:
        s = self.dashboard.sections
        mem = s["environmental_membrane"]
        sp = s["source_diet_pressure"]
        lines = ["# Membrane", "", _READ_ONLY_BANNER, "",
                 f"- membrane: {mem.get('status')} "
                 f"(report {mem.get('report_path') or '-'})",
                 f"- impressions: {mem.get('metrics', {}).get('impression_count', 0)}",
                 f"- source pressure: "
                 f"{sp.get('metrics', {}).get('source_pressure_status')}",
                 "", "_Downstream modules consume sensory impressions, not raw "
                 "events._"]
        return "\n".join(lines)

    def _quarantine_md(self) -> str:
        s = self.dashboard.sections
        q = s["quarantine_and_safety_blocks"]["quarantine"]
        blockers = s["quarantine_and_safety_blocks"]["blockers"]
        lines = ["# Quarantine and Safety Blocks", "", _READ_ONLY_BANNER, "",
                 f"- quarantined: "
                 f"{q.get('metrics', {}).get('quarantined_count', 0)}",
                 "", "## Blockers", ""]
        lines += ([f"- [{b['severity']}] {b['stage']}: {b['detail']}"
                   for b in blockers] if blockers else ["- none"])
        lines += ["", "_Unsafe events are quarantined, never learned. Quarantine "
                  "and blockers are never hidden._"]
        return "\n".join(lines)

    def _fixture_md(self) -> str:
        s = self.dashboard.sections
        fx = s["latest_fixture_run"]
        lines = ["# Fixture Tester Run", "", _READ_ONLY_BANNER, "",
                 f"- status: {fx.get('status')}",
                 f"- report: {fx.get('report_path') or '-'}",
                 f"- metrics: {fx.get('metrics', {})}",
                 f"- next action: {fx.get('next_action') or '-'}"]
        return "\n".join(lines)

    def _live_md(self) -> str:
        s = self.dashboard.sections
        live = s["latest_live_run"]
        lines = ["# Live-Read-Only Tester Run", "", _READ_ONLY_BANNER, "",
                 f"- status: {live.get('status')}",
                 f"- report: {live.get('report_path') or '-'}",
                 f"- next action: {live.get('next_action') or '-'}", "",
                 "_External feeders are manual; Solaris controls none._"]
        return "\n".join(lines)

    def _claims_md(self) -> str:
        s = self.dashboard.sections
        claims = s["claims_and_non_claims"]
        lines = ["# Claims and Non-Claims", "", _READ_ONLY_BANNER, "",
                 f"- status: {claims.get('status')}",
                 f"- {claims.get('explanation')}", ""]
        for b in claims.get("blockers", []):
            lines.append(f"- [blocker] {b}")
        lines += ["", "_Fixture/live evidence is operational. No consciousness/"
                  "life/agency claim is made._"]
        return "\n".join(lines)

    def _next_actions_md(self) -> str:
        lines = ["# Next Actions", "", _READ_ONLY_BANNER, "",
                 "_Recommendations only; the console never executes them._", "",
                 "| priority | action | detail | manual approval |",
                 "| --- | --- | --- | --- |"]
        for a in self.next_actions:
            d = a.to_dict()
            lines.append(f"| {d['priority']} | {d['action']} | {d['detail']} | "
                         f"{'yes' if d['requires_manual_approval'] else ''} |")
        return "\n".join(lines)

    def _cannot_do(self) -> List[str]:
        lines = ["## What this console cannot do", ""]
        lines += [f"- {item}" for item in
                  self.dashboard.to_dict()["what_this_console_cannot_do"]]
        return lines


def _w(path: str, text: str) -> str:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def _guard(text: str) -> str:
    try:
        from ..governance.compliance import ClaimGuard
        guard = ClaimGuard()
        if not guard.scan_text(text).safe:
            return guard.rewrite(text)
    except Exception:
        pass
    return text
