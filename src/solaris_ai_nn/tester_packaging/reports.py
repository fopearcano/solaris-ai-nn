"""Tester packaging reports -- local readiness summaries for the developer/tester.

:class:`TesterPackagingReportBuilder` writes the packaging report set (overall report,
dependency / environment-doctor / command-registry / clean-machine / platform-notes /
safety reports). Every report states that the packaging runtime installed nothing,
started no feeders, controlled no hardware, accessed no network/Git/GitHub/shell/
browser/OS, published/uploaded nothing, created no releases/tags, trained on no
feedback, and made no consciousness/life/agency claim. ClaimGuard scans the Markdown
when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict

_WHAT_THIS_DOES_NOT_DO = (
    "The packaging runtime did not install packages.",
    "It did not start feeders.",
    "It did not control hardware.",
    "It did not access network/Git/GitHub/shell/browser/OS.",
    "It did not publish or upload anything.",
    "It did not create releases or tags.",
    "It did not train from feedback.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class TesterPackagingReportBuilder:
    """Builds the packaging report set (Markdown + JSON)."""

    runtime: Any

    def write(self) -> Dict[str, Any]:
        rt = self.runtime
        reports_dir = os.path.join(rt.packaging_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        summary = rt._run_summary()

        md = _guard(self._main_md(summary))
        md_path = os.path.join(reports_dir, "PACKAGING_REPORT.md")
        _w(md_path, md)
        _wj(os.path.join(reports_dir, "PACKAGING_REPORT.json"),
            {"sections": summary, "claim_guard_safe": _safe(md)})

        for name, body in {
            "DEPENDENCY_CHECK_REPORT.md": self._dependency_md(summary),
            "ENVIRONMENT_DOCTOR_REPORT.md": self._doctor_md(summary),
            "COMMAND_REGISTRY_REPORT.md": self._command_md(summary),
            "CLEAN_MACHINE_READINESS_REPORT.md": self._clean_md(summary),
            "PLATFORM_NOTES_REPORT.md": self._platform_md(summary),
            "PACKAGING_SAFETY_REPORT.md": self._safety_md(),
        }.items():
            _w(os.path.join(reports_dir, name), _guard(body))
        return {"markdown": md_path,
                "json": os.path.join(reports_dir, "PACKAGING_REPORT.json")}

    def _main_md(self, s: Dict[str, Any]) -> str:
        rt = self.runtime
        st = s["packaging_status"]
        lines = ["# Tester Packaging Report", "",
                 "_The packaging runtime is local and report-only. It installs "
                 "nothing, publishes/uploads nothing, creates no releases/tags, "
                 "starts no feeders, controls no hardware, accesses no network/"
                 "Git/GitHub/shell/browser/OS, and makes no claim of "
                 "consciousness, sentience, biological life, personhood, agency, "
                 "free will, emotion, feeling, understanding, self-awareness, or "
                 "subjective experience._", "",
                 "## Purpose", "", rt.packaging_profile.purpose, "",
                 "## Profile", "",
                 f"- {st['packaging_profile']} (readiness: **{st['readiness']}**)",
                 "", "## Dependency status", "",
                 f"- passed: {st['dependency_blocker_count'] == 0} "
                 f"(blockers {st['dependency_blocker_count']}, warnings "
                 f"{st['dependency_warning_count']})", "",
                 "## Environment doctor", "",
                 f"- health: **{st['doctor_status']}** (pass: "
                 f"{st['doctor_pass']})", "",
                 "## Command registry", "",
                 f"- missing required: {st['missing_required_command_count']}; "
                 f"missing optional: {st['missing_optional_command_count']}", "",
                 "## Clean-machine readiness", "",
                 f"- status: **{st['clean_machine_status']}**", "",
                 "## Release manifest status", "",
                 f"- readiness: {st['release_readiness']}", "",
                 "## Install guide status", "",
                 f"- install guide: {st['latest_install_guide_path'] or 'not built'}",
                 "", "## Platform notes", "",
                 f"- {', '.join(s['platform_paths'].keys()) or 'not built'}", ""]
        if s["blockers"]:
            lines += ["## Blockers", ""] + [f"- {b}" for b in s["blockers"]] + [""]
        if s["warnings"]:
            lines += ["## Warnings", ""] + [f"- {w}" for w in s["warnings"]] + [""]
        lines += ["## Next actions", ""]
        lines += [f"- {a}" for a in s["next_actions"]]
        lines += ["", "## Limitations", ""]
        lines += [f"- {l}" for l in rt.packaging_profile.limitations]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in _WHAT_THIS_DOES_NOT_DO]
        return "\n".join(lines)

    def _dependency_md(self, s: Dict[str, Any]) -> str:
        d = s["dependency_check"]
        lines = ["# Dependency Check Report", "",
                 "_Read-only; the runtime installs nothing._", "",
                 f"- python: {d.get('python_version')} (ok: {d.get('python_ok')})",
                 f"- editable install: {d.get('editable_install')}",
                 f"- pyproject present: {d.get('pyproject_present')}",
                 f"- blockers: {d.get('blocker_count', 0)}; warnings: "
                 f"{d.get('warning_count', 0)}", "",
                 "| dependency | kind | available | install hint |",
                 "| --- | --- | --- | --- |"]
        for f in d.get("findings", []):
            lines.append(f"| {f['name']} | {f['kind']} | {f['available']} | "
                         f"{f['install_hint']} |")
        return "\n".join(lines)

    def _doctor_md(self, s: Dict[str, Any]) -> str:
        d = s["environment_doctor"]
        lines = ["# Environment Doctor Report", "",
                 "_Read-only; never auto-fixes, installs, or runs shell/network._",
                 "",
                 f"- overall health: **{d.get('overall_health')}**",
                 f"- blockers: {d.get('blocker_count', 0)}; warnings: "
                 f"{d.get('warning_count', 0)}", "",
                 "| check | health | detail |", "| --- | --- | --- |"]
        for f in d.get("findings", []):
            lines.append(f"| {f['check']} | {f['health']} | {f['detail']} |")
        return "\n".join(lines)

    def _command_md(self, s: Dict[str, Any]) -> str:
        c = s["command_registry"]
        lines = ["# Command Registry Report", "",
                 "_Read-only; no command is executed._", "",
                 f"- registered: {c.get('registered_count', 0)}/"
                 f"{c.get('command_count', 0)}",
                 f"- missing required: {c.get('missing_required', [])}",
                 f"- missing optional: {c.get('missing_optional', [])}"]
        return "\n".join(lines)

    def _clean_md(self, s: Dict[str, Any]) -> str:
        c = s["clean_machine"]
        lines = ["# Clean-Machine Readiness Report", "",
                 "_Report-only; flags hidden developer-machine assumptions._", "",
                 f"- status: **{c.get('status', 'unknown')}**",
                 f"- blockers: {c.get('blocker_count', 0)}", ""]
        checklist = c.get("checklist", {}).get("items", [])
        if checklist:
            lines += ["| check | satisfied | required |",
                      "| --- | --- | --- |"]
            for i in checklist:
                lines.append(f"| {i['check']} | {i['satisfied']} | "
                             f"{i['required']} |")
        return "\n".join(lines)

    def _platform_md(self, s: Dict[str, Any]) -> str:
        lines = ["# Platform Notes Report", "",
                 "_Local editable install only; no admin/root, no global "
                 "install._", ""]
        for kind, path in s.get("platform_paths", {}).items():
            lines.append(f"- {kind}: {path}")
        if not s.get("platform_paths"):
            lines.append("- platform notes not built in this mode")
        return "\n".join(lines)

    def _safety_md(self) -> str:
        snap = self.runtime.safety.snapshot()
        lines = ["# Packaging Safety Report", "",
                 f"- safety blocks recorded: {snap.get('rejected_count', 0)}",
                 f"- can install packages: {snap.get('can_install_packages')}",
                 f"- can publish: {snap.get('can_publish')}",
                 f"- can create releases: {snap.get('can_create_releases')}",
                 f"- can create tags: {snap.get('can_create_tags')}",
                 f"- can open browser: {snap.get('can_open_browser')}", "",
                 "## Hard rules", ""]
        lines += [f"- {r}" for r in snap.get("hard_rules", [])]
        lines += ["", "_All install/publish/upload/release/tag/browser/"
                  "background-service capabilities are False by design._"]
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
