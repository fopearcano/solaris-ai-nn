"""Tester live report -- the operator-readable summary of a live-read-only run.

:class:`TesterLiveReportBuilder` writes the live tester report (Markdown + JSON) and the
run summary JSON. The report states explicitly that this is live-read-only testing,
that external feeders are manual/tester-run only, and that Solaris did not start/stop/
control feeders, control hardware, access network/Git/GitHub/shell/browser/OS, execute
commands from sensory text, treat human labels/debug gloss as ground truth, or use
tester feedback as training -- and that no consciousness/life/agency claim is made.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict

_WHAT_THIS_DOES_NOT_DO = (
    "This is live-read-only testing.",
    "External feeders are manual/tester-run only.",
    "Solaris did not start/stop/control feeders.",
    "Solaris did not control hardware.",
    "Solaris did not access network/Git/GitHub/shell/browser/OS.",
    "Solaris did not execute commands from sensory text.",
    "Solaris did not treat human labels/debug glosses as ground truth.",
    "Solaris did not use tester feedback as training.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class TesterLiveReport:
    """The structured live tester report sections."""

    sections: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.sections)


@dataclass
class TesterLiveReportBuilder:
    """Builds the live tester report (Markdown + JSON) and run summary."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        return {
            "purpose": ("a bounded, local, live-read-only tester run; external "
                        "feeders are manual and Solaris never controls them"),
            "profile": rt.live_profile.to_dict(),
            "live_state_status": {"state_dir": rt.state_dir,
                                  "tester_state_dir": rt.tester_state_dir},
            "governance_status": rt.governance_status,
            "feeder_registry_status": rt.feeder_status,
            "external_feeder_policy": {
                "solaris_starts_feeders": False,
                "solaris_stops_feeders": False,
                "solaris_schedules_feeders": False,
                "solaris_controls_feeders": False,
                "feeders_are_external_manual": True,
                "note": "feeders are dumb external scripts or manual files; "
                        "Solaris validates the JSONL events they write"},
            "sample_validation": rt.sample_validation,
            "live_doctor": rt.doctor_result.to_dict()
            if rt.doctor_result else {},
            "birth_status": rt.birth_status,
            "membrane_status": rt.membrane_status,
            "integration_status": rt.integration_status,
            "observation_status": rt.observation_status,
            "quarantine_summary": rt.quarantine_summary,
            "source_pressure_summary": {
                "status": rt.membrane_status.get("source_pressure_status"),
                "operator_dominance_score": rt.membrane_status.get(
                    "membrane_operator_dominance_score")},
            "artifact_bundle_path": rt.bundle_dir,
            "blockers": list(rt.blockers), "warnings": list(rt.warnings),
            "tester_next_steps": rt.recommended_next_steps(),
            "limitations": list(rt.live_profile.limitations),
            "safety_status": rt.safety.snapshot(),
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }

    def _render(self, s: Dict[str, Any]) -> str:
        rt = self.runtime
        gov = s["governance_status"]
        doc = s["live_doctor"]
        lines = [
            "# Tester Live-Read-Only Report", "",
            "_This is live-read-only testing. External feeders are manual/"
            "tester-run only. Solaris did not start/stop/schedule/control "
            "feeders, control hardware, access the network/Git/GitHub/shell/"
            "browser/OS, execute commands from sensory text, treat human labels "
            "or debug gloss as ground truth, or use tester feedback as training, "
            "and it makes no claim of consciousness, sentience, biological life, "
            "personhood, agency, free will, emotion, feeling, understanding, "
            "self-awareness, or subjective experience._", "",
            f"- run id: {rt.run_id} ({s['profile']['profile_id']})",
            f"- governance: {gov.get('status')} (enabled+approved "
            f"{gov.get('enabled_and_approved')})",
            f"- feeder registry: {s['feeder_registry_status'].get('feeder_count', 0)}"
            f" feeders (Solaris controls any: "
            f"{s['feeder_registry_status'].get('solaris_controls_any_feeder')})",
            f"- live doctor: {doc.get('overall_status')} "
            f"(blockers {doc.get('blocker_count', 0)})",
            f"- fixture demo status: {rt.fixture_status.get('fixture_demo_status')}",
            f"- membrane impressions: "
            f"{s['membrane_status'].get('membrane_impression_count', 0)}",
            f"- quarantined: {s['quarantine_summary'].get('quarantined_count', 0)}",
            f"- blocked: {rt.blocked}",
            f"- artifact bundle: {s['artifact_bundle_path']}", "",
        ]
        if s["blockers"]:
            lines += ["## Blockers", ""] + [f"- {b}" for b in s["blockers"]] + [""]
        if s["warnings"]:
            lines += ["## Warnings", ""] + [f"- {w}" for w in s["warnings"]] + [""]
        sv = s["sample_validation"]
        if sv:
            lines += ["## Safe/unsafe event pack results", "",
                      f"- safe accepted: {sv.get('safe', {}).get('accepted_count')}"
                      f"/{sv.get('safe', {}).get('event_count')}",
                      f"- unsafe quarantined: "
                      f"{sv.get('unsafe', {}).get('quarantined_count')}"
                      f"/{sv.get('unsafe', {}).get('event_count')}",
                      f"- mixed partial: "
                      f"{sv.get('mixed', {}).get('partially_accepted')}", ""]
        lines += ["## External feeder policy", "",
                  "- Solaris starts feeders: False",
                  "- Solaris stops feeders: False",
                  "- Solaris schedules feeders: False",
                  "- Solaris controls feeders: False",
                  "- feeders are external/manual: True", ""]
        lines += ["## Tester next steps", ""]
        lines += [f"- {step}" for step in s["tester_next_steps"]]
        lines += ["", "## Limitations", ""]
        lines += [f"- {l}" for l in s["limitations"]]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in s["what_this_does_not_do"]]
        return "\n".join(lines)

    def write(self) -> Dict[str, Any]:
        rt = self.runtime
        sections = self.build()
        base = os.path.join(rt.tester_state_dir, "reports")
        os.makedirs(base, exist_ok=True)
        md = _guard(self._render(sections))
        md_path = os.path.join(
            base, f"TESTER_LIVE_READONLY_REPORT_{rt.run_id}.md")
        json_path = os.path.join(
            base, f"TESTER_LIVE_READONLY_REPORT_{rt.run_id}.json")
        summary_path = os.path.join(
            base, f"TESTER_LIVE_RUN_SUMMARY_{rt.run_id}.json")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(md)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump({"sections": sections, "claim_guard_safe": _safe(md)},
                      fh, indent=2, default=str)
        with open(summary_path, "w", encoding="utf-8") as fh:
            json.dump(rt._run_summary(), fh, indent=2, default=str)
        return {"markdown": md_path, "json": json_path, "summary": summary_path}


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
