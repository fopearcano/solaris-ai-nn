"""Tester safety-freeze reports -- the release-gate report set.

:class:`TesterSafetyFreezeReportBuilder` writes the safety-freeze report set (overall
freeze report, claim freeze, capability freeze, artifact scan, red-team, release
blockers). Every report states the safety freeze is a tester-release gate only (it does
not prove the system safe in general) and that no feeder/hardware/network/Git/publish/
release/feedback-training occurred. ClaimGuard scans the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict

_WHAT_THIS_DOES_NOT_DO = (
    "The safety freeze does not prove the system safe in general.",
    "The safety freeze is a tester-release gate only.",
    "No feeder was started/stopped/controlled.",
    "No hardware was controlled.",
    "No network/Git/GitHub/shell/browser/OS access occurred.",
    "No artifacts were uploaded/published.",
    "No GitHub issues/releases/tags were created.",
    "No feedback was used as training.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class TesterSafetyFreezeReportBuilder:
    """Builds the safety-freeze report set (Markdown + JSON)."""

    runtime: Any

    def write(self) -> Dict[str, Any]:
        rt = self.runtime
        reports = os.path.join(rt.safety_freeze_dir, "reports")
        os.makedirs(reports, exist_ok=True)
        s = rt._run_summary()

        md = _guard(self._main_md(s))
        md_path = os.path.join(reports, "TESTER_SAFETY_FREEZE_REPORT.md")
        _w(md_path, md)
        _wj(os.path.join(reports, "TESTER_SAFETY_FREEZE_REPORT.json"),
            {"sections": s, "claim_guard_safe": _safe(md)})

        _w(os.path.join(reports, "TESTER_CLAIM_FREEZE_REPORT.md"),
           _guard(self._claim_md(s)))
        _wj(os.path.join(reports, "TESTER_CLAIM_FREEZE_REPORT.json"),
            s["claim_freeze"])
        _w(os.path.join(reports, "TESTER_CAPABILITY_FREEZE_REPORT.md"),
           _guard(self._capability_md(s)))
        _wj(os.path.join(reports, "TESTER_CAPABILITY_FREEZE_REPORT.json"),
            s["capability_freeze"])
        _w(os.path.join(reports, "TESTER_ARTIFACT_SAFETY_SCAN.md"),
           _guard(self._artifact_md(s)))
        _w(os.path.join(reports, "TESTER_RED_TEAM_REPORT.md"),
           _guard(self._red_team_md(s)))
        _w(os.path.join(reports, "TESTER_RELEASE_BLOCKERS.md"),
           _guard(rt.blocker_gate.to_markdown() if rt.blocker_gate else ""))
        _wj(os.path.join(reports, "TESTER_RELEASE_BLOCKERS.json"),
            s["release_blockers"])
        return {"markdown": md_path,
                "json": os.path.join(reports,
                                     "TESTER_SAFETY_FREEZE_REPORT.json")}

    def _main_md(self, s: Dict[str, Any]) -> str:
        rt = self.runtime
        st = s["safety_freeze_status"]
        lines = ["# Tester Safety Freeze Report", "",
                 "_The safety freeze is a tester-release gate only; it does NOT "
                 "prove the system safe in general. No feeder/hardware/network/"
                 "Git/GitHub/shell/browser/OS access occurred, nothing was "
                 "uploaded/published, no releases/tags/issues were created, no "
                 "feedback was used as training, and no claim of consciousness, "
                 "sentience, biological life, personhood, agency, free will, "
                 "emotion, feeling, understanding, self-awareness, or subjective "
                 "experience is made._", "",
                 "## Purpose", "", rt.safety_freeze_profile.purpose, "",
                 "## Profile", "",
                 f"- {st['safety_freeze_profile']} (readiness: "
                 f"**{st['readiness']}**)", "",
                 "## Claim freeze summary", "",
                 f"- forbidden claims: {st['forbidden_claim_count']}; warnings: "
                 f"{st['claim_warning_count']}; missing disclaimers: "
                 f"{st['missing_disclaimer_count']}", "",
                 "## Capability freeze summary", "",
                 f"- capability blockers: {st['capability_blocker_count']}", "",
                 "## Red-team checklist summary", "",
                 f"- pass: {st['red_team_pass']}; blockers: "
                 f"{st['red_team_blocker_count']}", "",
                 "## Artifact scan summary", "",
                 f"- blockers: {s['artifact_scan'].get('blocker_count', 0)}; "
                 f"warnings: {s['artifact_scan'].get('warning_count', 0)}", "",
                 "## Release blockers", "",
                 f"- open: {st['release_blocker_count']} (critical "
                 f"{st['critical_blocker_count']}); release candidate allowed: "
                 f"{st['release_candidate_allowed']}"]
        blockers = s["release_blockers"].get("blockers", [])
        for b in blockers:
            if b["is_open"]:
                lines.append(f"  - [{b['category']}] {b['detail']}")
        lines += ["", "## Warnings", ""]
        lines += [f"- {w}" for w in s["warnings"]] or ["- none"]
        waived = s["release_blockers"].get("blockers", [])
        waived = [b for b in waived if b["status"] == "waived_for_tester_release"]
        lines += ["", "## Waivers", ""]
        lines += [f"- {b['blocker_id']}: {b['waiver_reason']}" for b in waived] \
            or ["- none"]
        lines += ["", "## Missing disclaimers", ""]
        missing = s["claim_freeze"].get("missing_disclaimers", [])
        lines += [f"- {m}" for m in missing] or ["- none"]
        lines += ["", "## Readiness recommendation", "",
                  f"- **{st['readiness']}**", "",
                  "## Next action", "", f"- {s['next_action']}", "",
                  "## Limitations", ""]
        lines += [f"- {l}" for l in rt.safety_freeze_profile.limitations]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in _WHAT_THIS_DOES_NOT_DO]
        return "\n".join(lines)

    def _claim_md(self, s: Dict[str, Any]) -> str:
        c = s["claim_freeze"]
        lines = ["# Tester Claim Freeze Report", "",
                 "_Forbidden consciousness/life/agency claims are release "
                 "blockers; missing disclaimers in tester docs are blockers._",
                 "",
                 f"- scanned files: {c.get('scanned_files', 0)}",
                 f"- forbidden claims: {c.get('forbidden_claim_count', 0)}",
                 f"- release blockers: {c.get('release_blocker_count', 0)}",
                 f"- by category: {c.get('by_category', {})}", "",
                 "| path | line | category | severity | replacement |",
                 "| --- | --- | --- | --- | --- |"]
        for f in c.get("findings", []):
            lines.append(f"| {f['path']} | {f['line']} | {f['category']} | "
                         f"{f['severity']} | {f['replacement']} |")
        if not c.get("findings"):
            lines.append("| (none) | | | | |")
        return "\n".join(lines)

    def _capability_md(self, s: Dict[str, Any]) -> str:
        c = s["capability_freeze"]
        lines = ["# Tester Capability Freeze Report", "",
                 "_Any active-control implication blocks the tester release._", "",
                 f"- scanned files: {c.get('scanned_files', 0)}",
                 f"- blockers: {c.get('blocker_count', 0)}",
                 f"- by category: {c.get('by_category', {})}", "",
                 "| path | line | category | match |",
                 "| --- | --- | --- | --- |"]
        for f in c.get("findings", []):
            lines.append(f"| {f['path']} | {f['line']} | {f['category']} | "
                         f"{f['matched_text']} |")
        if not c.get("findings"):
            lines.append("| (none) | | | |")
        return "\n".join(lines)

    def _artifact_md(self, s: Dict[str, Any]) -> str:
        a = s["artifact_scan"]
        lines = ["# Tester Artifact Safety Scan", "",
                 "_Bounded text scan; binaries skipped; nothing executed._", "",
                 f"- scanned files: {a.get('scanned_files', 0)}",
                 f"- blockers: {a.get('blocker_count', 0)}; warnings: "
                 f"{a.get('warning_count', 0)}",
                 f"- by kind: {a.get('by_kind', {})}", "",
                 "| path | line | kind | severity | detail |",
                 "| --- | --- | --- | --- | --- |"]
        for f in a.get("findings", [])[:200]:
            lines.append(f"| {f['path']} | {f['line']} | {f['kind']} | "
                         f"{f['severity']} | {f['detail']} |")
        if not a.get("findings"):
            lines.append("| (none) | | | | |")
        return "\n".join(lines)

    def _red_team_md(self, s: Dict[str, Any]) -> str:
        r = s["red_team"]
        lines = ["# Tester Red-Team Report", "",
                 "_Failed critical checks become release blockers; unknown "
                 "critical checks block until reviewed._", "",
                 f"- pass: {r.get('pass_count', 0)}; fail: "
                 f"{r.get('fail_count', 0)}; unknown: {r.get('unknown_count', 0)}",
                 f"- blockers: {r.get('blocker_count', 0)}", "",
                 "| check | category | status | critical | blocking |",
                 "| --- | --- | --- | --- | --- |"]
        for c in r.get("checks", []):
            lines.append(f"| {c['check_id']} | {c['category']} | {c['status']} "
                         f"| {c['critical']} | {c['blocking']} |")
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
