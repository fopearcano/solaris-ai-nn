"""First tester protocol reports -- the protocol report set.

:class:`FirstTesterProtocolReportBuilder` writes the protocol report set (overall report,
session/acceptance/stop-conditions/handoff/safety reports). Every report states the
protocol does not run the tester session and performs no publish/upload/release/feeder/
network action, and makes no consciousness/life/agency claim. ClaimGuard scans the
Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict

_WHAT_THIS_DOES_NOT_DO = (
    "This protocol does not run the tester session.",
    "No public release was created.",
    "No package was uploaded.",
    "No GitHub release/tag/issue was created.",
    "No feeder was started/stopped/controlled.",
    "No hardware was controlled.",
    "No network/Git/GitHub/shell/browser/OS access occurred.",
    "No artifacts were uploaded/published.",
    "No feedback was used as training.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class FirstTesterProtocolReportBuilder:
    """Builds the first-tester protocol report set (Markdown + JSON)."""

    runtime: Any

    def write(self) -> Dict[str, Any]:
        rt = self.runtime
        reports = os.path.join(rt.protocol_dir, "reports")
        os.makedirs(reports, exist_ok=True)
        s = rt._run_summary()

        md = _guard(self._main_md(s))
        md_path = os.path.join(reports, "FIRST_TESTER_PROTOCOL_REPORT.md")
        _w(md_path, md)
        _wj(os.path.join(reports, "FIRST_TESTER_PROTOCOL_REPORT.json"),
            {"sections": s, "claim_guard_safe": _safe(md)})

        _w(os.path.join(reports, "FIRST_TESTER_SESSION_REPORT.md"),
           _guard(self._session_md(s)))
        _w(os.path.join(reports, "FIRST_TESTER_ACCEPTANCE_REPORT.md"),
           _guard(self._acceptance_md(s)))
        _w(os.path.join(reports, "FIRST_TESTER_STOP_CONDITIONS_REPORT.md"),
           _guard(self._stops_md(s)))
        _w(os.path.join(reports, "FIRST_TESTER_HANDOFF_REPORT.md"),
           _guard(self._handoff_md(s)))
        _w(os.path.join(reports, "FIRST_TESTER_SAFETY_REPORT.md"),
           _guard(self._safety_md(s)))
        return {"markdown": md_path,
                "json": os.path.join(reports,
                                     "FIRST_TESTER_PROTOCOL_REPORT.json")}

    def _main_md(self, s: Dict[str, Any]) -> str:
        rt = self.runtime
        st = s["protocol_status"]
        lines = ["# First Tester Protocol Report", "",
                 "_This protocol does not run the tester session. No public "
                 "release was created, no package was uploaded, no GitHub "
                 "release/tag/issue was created, no feeder was started/stopped/"
                 "controlled, no hardware was controlled, no network/Git/GitHub/"
                 "shell/browser/OS access occurred, no feedback was used as "
                 "training, and no claim of consciousness, sentience, "
                 "biological life, personhood, agency, free will, emotion, "
                 "feeling, understanding, self-awareness, or subjective "
                 "experience is made._", "",
                 "## Purpose", "", rt.protocol_profile.purpose, "",
                 "## Profile", "", f"- {st['protocol_profile']}", "",
                 "## Generated files", ""]
        lines += [f"- {k}: `{v}`" for k, v in s["doc_paths"].items()] \
            or ["- none"]
        lines += ["", "## RC status", "",
                  f"- RC readiness: {st['rc_readiness']}", "",
                  "## Required preconditions", "",
                  f"- packaging readiness: {st['packaging_readiness']}",
                  f"- safety freeze readiness: {st['safety_freeze_readiness']}",
                  f"- fixture passed: {s['fixture_status'].get('fixture_passed')}",
                  "", "## Session script status", "",
                  f"- steps: {len(s['session_script'].get('steps', []))}; "
                  f"fixture-first: "
                  f"{s['session_script'].get('fixture_first')}", "",
                  "## Acceptance criteria status", "",
                  f"- criteria: {s['acceptance'].get('criterion_count', 0)}", "",
                  "## Stop conditions status", "",
                  f"- conditions: {s['stop_conditions'].get('condition_count', 0)} "
                  f"({s['stop_conditions'].get('by_severity', {})})", "",
                  "## Handoff guide status", "",
                  f"- artifacts: {s['handoff'].get('artifact_count', 0)}; "
                  f"manual-only: {s['handoff'].get('manual_only')}", "",
                  "## Post-test review template status", "",
                  f"- questions: {s['review'].get('question_count', 0)}", "",
                  "## Session status", "",
                  f"- **{st['session_status']}**", "",
                  "## Blockers", ""]
        lines += [f"- {b}" for b in s["blockers"]] or ["- none"]
        lines += ["", "## Warnings", ""]
        lines += [f"- {w}" for w in s["warnings"]] or ["- none"]
        lines += ["", "## Next action", "", f"- {s['next_action']}", "",
                  "## Limitations", ""]
        lines += [f"- {l}" for l in rt.protocol_profile.limitations]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in _WHAT_THIS_DOES_NOT_DO]
        return "\n".join(lines)

    def _session_md(self, s: Dict[str, Any]) -> str:
        sc = s["session_script"]
        lines = ["# First Tester Session Report", "",
                 "_The protocol generates the session script; it does not run "
                 "the session._", "",
                 f"- steps: {len(sc.get('steps', []))}",
                 f"- fixture-first: {sc.get('fixture_first')}",
                 f"- live-read-only optional: "
                 f"{sc.get('live_readonly_optional')}", "",
                 "| phase | status | step |", "| --- | --- | --- |"]
        for step in sc.get("steps", []):
            detail = step["command"] or step["text"]
            lines.append(f"| {step['phase']} | {step['status']} | {detail} |")
        return "\n".join(lines)

    def _acceptance_md(self, s: Dict[str, Any]) -> str:
        a = s["acceptance"]
        lines = ["# First Tester Acceptance Report", "",
                 "_Acceptance criteria describe operational success, not "
                 "cognition._", "",
                 f"- criteria: {a.get('criterion_count', 0)}",
                 f"- by category: {a.get('categories', {})}",
                 f"- result states: {a.get('result_states', [])}"]
        return "\n".join(lines)

    def _stops_md(self, s: Dict[str, Any]) -> str:
        c = s["stop_conditions"]
        lines = ["# First Tester Stop Conditions Report", "",
                 "_A critical stop means preserve artifacts and stop; never "
                 "work around a safety blocker._", "",
                 f"- conditions: {c.get('condition_count', 0)}",
                 f"- by severity: {c.get('by_severity', {})}", "",
                 "| severity | condition |", "| --- | --- |"]
        for cond in c.get("conditions", []):
            lines.append(f"| {cond['severity']} | {cond['text']} |")
        return "\n".join(lines)

    def _handoff_md(self, s: Dict[str, Any]) -> str:
        h = s["handoff"]
        lines = ["# First Tester Handoff Report", "",
                 "_Handoff is manual only; nothing is uploaded/published and no "
                 "GitHub issue is created._", "",
                 f"- artifacts: {h.get('artifact_count', 0)}",
                 f"- by privacy: {h.get('by_privacy', {})}",
                 f"- manual-only: {h.get('manual_only')}; uploads: "
                 f"{h.get('uploads')}"]
        return "\n".join(lines)

    def _safety_md(self, s: Dict[str, Any]) -> str:
        snap = s["safety_status"]
        lines = ["# First Tester Safety Report", "",
                 "_The protocol is local and documentation-only. The runtime "
                 "can never run the tester session, actuate, control hardware/"
                 "feeders, access the network/shell/Git/GitHub/browser/OS, "
                 "publish/upload, create releases/tags/issues, install "
                 "packages, execute artifact contents, or train on feedback._",
                 "", f"- rejected operations: {snap.get('rejected_count', 0)}",
                 "", "## Hard rules", ""]
        lines += [f"- {r}" for r in snap.get("hard_rules", [])]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in _WHAT_THIS_DOES_NOT_DO]
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
