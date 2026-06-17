"""Tester live-read-only report set -- spine, doctor, checklist, packs, bundle, safety.

:class:`TesterLiveReadOnlyReportBuilder` writes the tester live-read-only report set.
Every report states explicitly that this is live-read-only testing with external,
manual feeders, that Solaris controls no feeders/hardware/network/Git, and that no
consciousness/life/agency claim is made. ClaimGuard scans the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict

from .live_tester_checklist import TesterLiveChecklist

_DISCLAIMER = (
    "_This is live-read-only testing. External feeders are dumb, manual, and "
    "tester-run; Solaris never starts/stops/schedules/controls them. Solaris "
    "controls no hardware, accesses no network/Git/GitHub/shell/browser/OS, "
    "executes no command from sensory text, treats no human label or debug gloss "
    "as ground truth, uses no tester feedback as training, publishes/uploads "
    "nothing, and makes no claim of consciousness, sentience, biological life, "
    "personhood, agency, free will, emotion, feeling, understanding, "
    "self-awareness, or subjective experience._"
)


@dataclass
class TesterLiveReadOnlyReportBuilder:
    """Builds the tester live-read-only report set (Markdown + JSON)."""

    runtime: Any

    def write(self) -> Dict[str, Any]:
        rt = self.runtime
        base = os.path.join(rt.tester_state_dir, "reports")
        os.makedirs(base, exist_ok=True)
        written: Dict[str, str] = {}

        spine = self._spine_sections()
        spine_md = _guard(self._spine_md(spine))
        _write(os.path.join(base, "TESTER_LIVE_READONLY_SPINE_REPORT.md"),
               spine_md)
        _write_json(os.path.join(base, "TESTER_LIVE_READONLY_SPINE_REPORT.json"),
                    {"sections": spine, "claim_guard_safe": _safe(spine_md)})

        _write(os.path.join(base, "TESTER_LIVE_DOCTOR_REPORT.md"),
               _guard(self._doctor_md()))
        _write(os.path.join(base, "TESTER_LIVE_CHECKLIST.md"),
               _guard(TesterLiveChecklist.build().to_markdown()))
        _write(os.path.join(base, "TESTER_SAFE_EVENT_PACK_REPORT.md"),
               _guard(self._pack_md()))
        _write(os.path.join(base, "TESTER_FEEDER_TEMPLATE_REPORT.md"),
               _guard(self._feeder_md()))
        _write(os.path.join(base, "TESTER_LIVE_BUNDLE_REPORT.md"),
               _guard(self._bundle_md()))
        safety_path = os.path.join(base, "TESTER_LIVE_SAFETY_REPORT.md")
        _write(safety_path, _guard(self._safety_md()))
        written["safety_markdown"] = safety_path
        rt.reports.setdefault("safety_markdown", safety_path)
        return written

    def _spine_sections(self) -> Dict[str, Any]:
        rt = self.runtime
        return {
            "purpose": "the safe bridge from fixture testing to trusted "
                       "live-read-only testing",
            "profile": rt.live_profile.to_dict(),
            "tester_live_status": rt.tester_live_status(),
            "governance_status": rt.governance_status,
            "feeder_status": rt.feeder_status,
            "sample_validation": rt.sample_validation,
        }

    def _spine_md(self, s: Dict[str, Any]) -> str:
        st = s["tester_live_status"]
        lines = ["# Tester Live-Read-Only Spine Report", "", _DISCLAIMER, "",
                 f"- run id: {st['tester_live_run_id']} "
                 f"({st['tester_live_profile']})",
                 f"- governance: {st['governance_status']} (enabled+approved "
                 f"{st['governance_enabled_and_approved']})",
                 f"- feeder registry present: {st['feeder_registry_present']}",
                 f"- live doctor: {st['live_doctor_status']}",
                 f"- membrane impressions: {st['membrane_impression_count']}",
                 f"- quarantined: {st['quarantine_count']}",
                 f"- blocked: {st['tester_live_blocked']}", "",
                 "_The first live tester path is read-only. External feeders are "
                 "manual; Solaris validates the JSONL events they write and the "
                 "membrane turns accepted events into sensory impressions._"]
        return "\n".join(lines)

    def _doctor_md(self) -> str:
        d = self.runtime.doctor_result.to_dict() if self.runtime.doctor_result \
            else {}
        lines = ["# Tester Live Doctor Report", "", _DISCLAIMER, "",
                 f"- overall status: {d.get('overall_status')}",
                 f"- findings: {d.get('finding_count', 0)} "
                 f"(blockers {d.get('blocker_count', 0)}, warnings "
                 f"{d.get('warning_count', 0)})", ""]
        for f in d.get("findings", []):
            lines.append(f"- [{f['status']}] {f['check']}"
                         + (f" -- {f['detail']}" if f["detail"] else ""))
        lines += ["", "_Missing/disabled governance, feeder control, or a "
                  "forbidden source blocks the live test._"]
        return "\n".join(lines)

    def _pack_md(self) -> str:
        sv = self.runtime.sample_validation or {}
        lines = ["# Tester Safe Event Pack Report", "", _DISCLAIMER, "",
                 f"- safe accepted: {sv.get('safe', {}).get('accepted_count', 0)}"
                 f"/{sv.get('safe', {}).get('event_count', 0)}",
                 f"- unsafe quarantined: "
                 f"{sv.get('unsafe', {}).get('quarantined_count', 0)}"
                 f"/{sv.get('unsafe', {}).get('event_count', 0)}",
                 f"- mixed partially accepted: "
                 f"{sv.get('mixed', {}).get('partially_accepted')}", "",
                 "_Safe events accept; unsafe events quarantine; mixed events "
                 "partially accept and partially quarantine. Debug gloss and "
                 "human labels are not ground truth._"]
        return "\n".join(lines)

    def _feeder_md(self) -> str:
        f = self.runtime.feeder_status or {}
        lines = ["# Tester Feeder Template Report", "", _DISCLAIMER, "",
                 f"- feeders: {f.get('feeder_count', 0)}",
                 f"- all external: {f.get('all_external')}",
                 f"- Solaris controls any feeder: "
                 f"{f.get('solaris_controls_any_feeder')}",
                 f"- invalid records: {f.get('invalid_record_count', 0)}", "",
                 "_The feeder registry is descriptive metadata only; all feeders "
                 "are external, read-only, operator-started, and never controlled "
                 "by Solaris. Unknown feeders are blocked by default._"]
        return "\n".join(lines)

    def _bundle_md(self) -> str:
        rt = self.runtime
        m = rt.bundle.manifest.to_dict() if rt.bundle else {}
        lines = ["# Tester Live Bundle Report", "", _DISCLAIMER, "",
                 f"- bundle dir: {m.get('bundle_dir', rt.bundle_dir)}",
                 f"- entries: {m.get('entry_count', 0)}",
                 f"- redactions: {', '.join(m.get('redactions', [])) or 'none'}",
                 f"- missing artifacts: "
                 f"{', '.join(m.get('missing_artifacts', [])) or 'none'}", "",
                 "_The live tester bundle is local-only and human-readable; "
                 "nothing is zipped automatically, uploaded, or published._"]
        return "\n".join(lines)

    def _safety_md(self) -> str:
        snap = self.runtime.safety.snapshot()
        lines = ["# Tester Live Safety Report", "", _DISCLAIMER, "",
                 f"- safety blocks recorded: {snap.get('rejected_count', 0)}",
                 f"- can start feeders: {snap.get('can_start_feeders')}",
                 f"- can schedule feeders: {snap.get('can_schedule_feeders')}",
                 f"- can execute feeder scripts: "
                 f"{snap.get('can_execute_feeder_scripts')}",
                 f"- can access network: {snap.get('can_access_network')}",
                 f"- can run git: {snap.get('can_run_git')}",
                 f"- tester feedback is training: "
                 f"{snap.get('tester_feedback_is_training')}", "",
                 "## Hard rules", ""]
        lines += [f"- {r}" for r in snap.get("hard_rules", [])]
        lines += ["", "_All feeder-control/scheduling/execution, hardware, "
                  "network/Git/publish, and feedback-training capabilities are "
                  "False by design._"]
        return "\n".join(lines)


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _write_json(path: str, obj: Any) -> None:
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
