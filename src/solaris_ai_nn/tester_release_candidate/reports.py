"""Tester RC reports -- the release-candidate report set.

:class:`TesterRCReportBuilder` writes the RC report set (overall RC report, readiness
report, artifact collection report, bundle report, safety report). Every report states
this is a local assembly step only -- no public release, no upload, no Git release/tag/
issue, no feeder/hardware/network access, no feedback training, and no consciousness/life/
agency claim. ClaimGuard scans the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict

_WHAT_THIS_DOES_NOT_DO = (
    "This is a local tester release-candidate assembly.",
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
class TesterRCReportBuilder:
    """Builds the RC report set (Markdown + JSON)."""

    runtime: Any

    def write(self) -> Dict[str, Any]:
        rt = self.runtime
        reports = os.path.join(rt.rc_dir, "reports")
        os.makedirs(reports, exist_ok=True)
        s = rt._run_summary()

        md = _guard(self._main_md(s))
        md_path = os.path.join(reports, "TESTER_RC_REPORT.md")
        _w(md_path, md)
        _wj(os.path.join(reports, "TESTER_RC_REPORT.json"),
            {"sections": s, "claim_guard_safe": _safe(md)})

        readiness_md = _guard(self._readiness_md(s))
        readiness_md_path = os.path.join(reports,
                                         "TESTER_RC_READINESS_REPORT.md")
        _w(readiness_md_path, readiness_md)
        _wj(os.path.join(reports, "TESTER_RC_READINESS_REPORT.json"),
            s["readiness"])

        _w(os.path.join(reports, "TESTER_RC_ARTIFACT_COLLECTION_REPORT.md"),
           _guard(self._artifact_md(s)))
        _w(os.path.join(reports, "TESTER_RC_BUNDLE_REPORT.md"),
           _guard(self._bundle_md(s)))
        _w(os.path.join(reports, "TESTER_RC_SAFETY_REPORT.md"),
           _guard(self._safety_md(s)))
        return {"markdown": md_path, "readiness_md": readiness_md_path,
                "json": os.path.join(reports, "TESTER_RC_REPORT.json")}

    def _main_md(self, s: Dict[str, Any]) -> str:
        rt = self.runtime
        st = s["rc_status"]
        col = s["artifact_collection"]
        lines = ["# Tester Release Candidate Report", "",
                 "_This is a local tester release-candidate assembly. No public "
                 "release was created, no package was uploaded, no GitHub "
                 "release/tag/issue was created, no feeder was started/stopped/"
                 "controlled, no hardware was controlled, no network/Git/GitHub/"
                 "shell/browser/OS access occurred, no feedback was used as "
                 "training, and no claim of consciousness, sentience, biological "
                 "life, personhood, agency, free will, emotion, feeling, "
                 "understanding, self-awareness, or subjective experience is "
                 "made._", "",
                 "## Purpose", "", rt.rc_profile.purpose, "",
                 "## Profile", "", f"- {st['rc_profile']}", "",
                 "## RC id", "", f"- `{st['rc_id']}`", "",
                 "## Readiness status", "",
                 f"- **{st['readiness']}** (gate: {st['rc_readiness_status']})",
                 f"- blockers: {st['blocker_count']} (critical "
                 f"{st['critical_blocker_count']}); warnings: "
                 f"{st['warning_count']}", "",
                 "## Artifact collection summary", "",
                 f"- present: {col.get('present_count', 0)} / "
                 f"{col.get('artifact_count', 0)}; missing required: "
                 f"{col.get('missing_required_count', 0)}; missing recommended: "
                 f"{col.get('missing_recommended_count', 0)}", "",
                 "## Packaging status", "",
                 f"- {s['ctx'].get('packaging', {}).get('readiness', 'unknown')}",
                 "", "## Safety freeze status", "",
                 f"- {s['ctx'].get('safety_freeze', {}).get('readiness', 'unknown')}",
                 "", "## Fixture tester status", "",
                 f"- fixture passed: "
                 f"{s['ctx'].get('fixture', {}).get('fixture_passed')}", "",
                 "## Live-read-only status", "",
                 f"- templates available: "
                 f"{s['ctx'].get('live', {}).get('templates_available')}", "",
                 "## Console status", "",
                 f"- read-only: "
                 f"{s['ctx'].get('console', {}).get('read_only')}", "",
                 "## Feedback status", "",
                 f"- non-training: "
                 f"{s['ctx'].get('feedback', {}).get('non_training')}", "",
                 "## Release blocker summary", ""]
        blockers = s["readiness"].get("blockers", [])
        lines += [f"- {'[critical] ' if b['critical'] else ''}{b['check']}: "
                  f"{b['detail']}" for b in blockers] or ["- none"]
        lines += ["", "## Generated docs", ""]
        lines += [f"- {k}: `{v}`" for k, v in s["doc_paths"].items()] \
            or ["- none"]
        lines += ["", "## Generated bundle path", "",
                  f"- `{st['latest_rc_bundle_path'] or 'not built'}`", "",
                  "## Missing artifacts", ""]
        lines += [f"- {k}" for k in col.get("missing_required", [])] or \
            ["- none required missing"]
        lines += ["", "## Warnings", ""]
        lines += [f"- {w}" for w in s["warnings"]] or ["- none"]
        lines += ["", "## Next action", "", f"- {s['next_action']}", "",
                  "## Limitations", ""]
        lines += [f"- {l}" for l in rt.rc_profile.limitations]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in _WHAT_THIS_DOES_NOT_DO]
        return "\n".join(lines)

    def _readiness_md(self, s: Dict[str, Any]) -> str:
        rt = self.runtime
        if rt.readiness:
            return rt.readiness.to_markdown()
        return "# Tester RC Readiness Report\n\n- status: unknown\n"

    def _artifact_md(self, s: Dict[str, Any]) -> str:
        col = s["artifact_collection"]
        lines = ["# Tester RC Artifact Collection Report", "",
                 "_Local artifact references only; no secrets or raw private "
                 "payloads are collected, and nothing is uploaded._", "",
                 f"- present: {col.get('present_count', 0)} / "
                 f"{col.get('artifact_count', 0)}", "",
                 "| key | tier | present | path |",
                 "| --- | --- | --- | --- |"]
        for a in col.get("artifacts", []):
            lines.append(f"| {a['key']} | {a['tier']} | {a['present']} | "
                         f"{a['path']} |")
        return "\n".join(lines)

    def _bundle_md(self, s: Dict[str, Any]) -> str:
        b = s["bundle"]
        if not b:
            return ("# Tester RC Bundle Report\n\n- no bundle built for this "
                    "profile\n")
        lines = ["# Tester RC Bundle Report", "",
                 "_Local RC bundle. Nothing was uploaded, published, tagged, or "
                 "released._", "",
                 f"- bundle dir: `{b.get('bundle_dir')}`",
                 f"- included: {b.get('included_count', 0)}; missing: "
                 f"{b.get('missing_count', 0)}",
                 f"- zipped: {b.get('zipped', False)}", "",
                 "## Included", ""]
        lines += [f"- {a['name']}" for a in b.get("included", [])] or ["- none"]
        lines += ["", "## Missing", ""]
        lines += [f"- {a['name']}" for a in b.get("missing", [])] or ["- none"]
        return "\n".join(lines)

    def _safety_md(self, s: Dict[str, Any]) -> str:
        snap = s["safety_status"]
        lines = ["# Tester RC Safety Report", "",
                 "_The RC assembly is local and assembly-only. The runtime can "
                 "never actuate, control hardware/feeders, access the network/"
                 "shell/Git/GitHub/browser/OS, publish/upload, create releases/"
                 "tags/issues, install packages, execute artifact contents, or "
                 "train on feedback._", "",
                 f"- rejected operations: {snap.get('rejected_count', 0)}", "",
                 "## Hard rules", ""]
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
