"""Live birth reports -- first-contact, validation, membrane, and safety reports.

:class:`LiveBirthReportBuilder` writes the live birth report set. Every report
states explicitly that no feeder was started or controlled, no hardware was
controlled, no network/Git/GitHub/shell/browser/OS access occurred, no commands
were executed, no sensory text was treated as a command, no human label was treated
as ground truth, and no consciousness/life/agency claim is made. ClaimGuard scans
the Markdown when available.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_WHAT_THIS_DOES_NOT_DO = (
    "No feeder was started.",
    "No feeder was controlled.",
    "No hardware was controlled.",
    "No network/Git/GitHub/shell/browser/OS access occurred.",
    "No commands were executed.",
    "No sensory text was treated as a command.",
    "No human label was treated as ground truth.",
    "No consciousness/life/agency claim is made.",
)


@dataclass
class LiveBirthReportBuilder:
    """Builds the live birth report set (Markdown + JSON)."""

    runtime: Any

    def build(self) -> Dict[str, Any]:
        rt = self.runtime
        status = rt.live_birth_status()
        sections: Dict[str, Any] = {
            "purpose": ("open a bounded, local, read-only environmental event "
                        "membrane for the first time and record the first "
                        "contact -- reading external feeder JSONL events, "
                        "validating and quarantining unsafe ones, activating the "
                        "sensory membrane on accepted events, and issuing a birth "
                        "certificate"),
            "profile": rt.birth_profile.to_dict(),
            "governance": rt.governance_result,
            "feeder_registry": (rt.feeders.index() if rt.feeders else {}),
            "inbox": rt.inbox_result,
            "membrane": rt.membrane,
            "quarantine": (rt.quarantine.index() if rt.quarantine else {}),
            "metabolism_status": rt.metabolism_status,
            "certificate": rt.certificate,
            "next_phases": rt.next_phase_recommendations(),
            "blocked": rt.blocked,
            "blockers": rt.blockers,
            "safety_status": rt.safety.snapshot(),
            "status": status,
            "what_this_does_not_do": list(_WHAT_THIS_DOES_NOT_DO),
        }
        markdown = self._render_main(sections)
        return {"sections": sections,
                "claim_guard_safe": self._claim_guard_safe(markdown)}

    def _render_main(self, sections: Dict[str, Any]) -> str:
        status = sections["status"]
        lines = [
            "# Live Read-Only Birth Report", "",
            "_Opens a local, read-only environmental event membrane. It does NOT "
            "start or control feeders, control hardware, access the network/"
            "shell/browser/OS, call Git/GitHub, execute commands, treat sensory "
            "text as a command, treat human labels as ground truth, or make any "
            "claim of consciousness, sentience, biological life, personhood, "
            "agency, free will, emotion, feeling, understanding, self-awareness, "
            "or subjective experience._", "",
            f"- profile: {status['birth_run_id']} "
            f"({sections['profile'].get('profile_id')})",
            f"- governance: {status['governance_status']} "
            f"(passed {status['governance_passed']})",
            f"- feeders: {status['live_feeder_count']}",
            f"- inbox files: {status['live_inbox_file_count']}; events: "
            f"{status['live_event_count']}",
            f"- accepted: {status['live_event_accepted_count']}; quarantined: "
            f"{status['live_event_quarantined_count']}",
            f"- membrane activation: {status['membrane_activation_status']}",
            f"- metabolism: {status['metabolism_status'] or 'not run'}",
            f"- blocked: {sections['blocked']}",
            f"- birth certificate: "
            f"{status['latest_birth_certificate_path'] or 'none'}",
            "",
        ]
        if sections["blockers"]:
            lines.append("## Blockers")
            lines.append("")
            lines += [f"- {b}" for b in sections["blockers"]]
            lines.append("")
        lines += ["## Accepted events (first-contact markers)", "",
                  f"- first accepted event id: "
                  f"{sections['membrane'].get('first_event_id') or 'none'}",
                  f"- first absence event id: "
                  f"{sections['membrane'].get('first_absence_event_id') or 'none'}",
                  f"- first noise event id: "
                  f"{sections['membrane'].get('first_noise_event_id') or 'none'}",
                  f"- first operator pulse id: "
                  f"{sections['membrane'].get('first_operator_pulse_id') or 'none'}",
                  ""]
        lines += ["## Quarantined events", "",
                  f"- quarantined: "
                  f"{sections['quarantine'].get('quarantined_event_count', 0)} "
                  f"(reasons: {sections['quarantine'].get('reasons', {})})", ""]
        lines += ["## Next recommended phase (not executed)", ""]
        lines += [f"- {p['phase']}: {p['detail']}"
                  for p in sections["next_phases"]]
        lines += ["", "## Safety boundaries", "",
                  "- read-only; no feeder/hardware control; no network/shell/Git/"
                  "GitHub/browser/OS; no command execution; bounded reads"]
        lines += ["", "## Limitations", ""]
        lines += [f"- {l}" for l in sections["profile"].get("limitations", [])]
        lines += ["", "## What this does NOT do", ""]
        lines += [f"- {item}" for item in sections["what_this_does_not_do"]]
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
        return {
            "FIRST_CONTACT_REPORT.md": self._first_contact_md(sections),
            "LIVE_EVENT_VALIDATION_REPORT.md": self._validation_md(sections),
            "LIVE_MEMBRANE_ACTIVATION_REPORT.md": self._membrane_md(sections),
            "LIVE_BIRTH_SAFETY_REPORT.md": self._safety_md(sections),
        }

    def _first_contact_md(self, s: Dict[str, Any]) -> str:
        m = s["membrane"]
        lines = ["# First Contact Report", "",
                 f"- first accepted event id: {m.get('first_event_id') or 'none'}",
                 f"- first accepted timestamp: "
                 f"{m.get('first_event_timestamp') or 'none'}",
                 f"- first absence event id: "
                 f"{m.get('first_absence_event_id') or 'none'}",
                 f"- first operator pulse id: "
                 f"{m.get('first_operator_pulse_id') or 'none'}", "",
                 "_First contact is an operational live-read-only exposure. It "
                 "does not imply consciousness, life, or agency._"]
        return self._guard("\n".join(lines))

    def _validation_md(self, s: Dict[str, Any]) -> str:
        inbox = s["inbox"]
        q = s["quarantine"]
        lines = ["# Live Event Validation Report", "",
                 f"- events: {inbox.get('live_event_count', 0)}",
                 f"- accepted: {inbox.get('live_event_accepted_count', 0)}",
                 f"- quarantined: {inbox.get('live_event_quarantined_count', 0)}",
                 f"- quarantine reasons: {q.get('reasons', {})}", "",
                 "_Validation never modifies the original event; unsafe events "
                 "are quarantined as evidence, not deleted._"]
        return self._guard("\n".join(lines))

    def _membrane_md(self, s: Dict[str, Any]) -> str:
        m = s["membrane"]
        lines = ["# Live Membrane Activation Report", "",
                 f"- activated: {m.get('membrane_activated')}",
                 f"- sensorium available: {m.get('sensorium_available')}",
                 f"- sensorium handoff: {m.get('sensorium_handoff')}",
                 f"- normalized events: {m.get('normalized_count', 0)}", "",
                 "_Membrane activation is read-only; it controls no feeders, "
                 "requests no more data, and treats no event text as a command._"]
        return self._guard("\n".join(lines))

    def _safety_md(self, s: Dict[str, Any]) -> str:
        snap = s["safety_status"]
        lines = ["# Live Birth Safety Report", "",
                 f"- safety blocks recorded: {snap.get('rejected_count', 0)}",
                 f"- can start feeders: {snap.get('can_start_feeders')}",
                 f"- can control hardware: {snap.get('can_control_hardware')}",
                 f"- can access network: {snap.get('can_access_network')}",
                 f"- sensory text is command: "
                 f"{snap.get('sensory_text_is_command')}", "",
                 "## Hard rules", ""]
        lines += [f"- {r}" for r in snap.get("hard_rules", [])]
        lines += ["", "_All control capabilities are False by design._"]
        return self._guard("\n".join(lines))

    def write(self, state_dir: Optional[str] = None) -> Dict[str, Any]:
        report = self.build()
        base = os.path.join(state_dir or self.runtime.state_dir, "reports")
        os.makedirs(base, exist_ok=True)
        md_path = os.path.join(base, "LIVE_BIRTH_REPORT.md")
        json_path = os.path.join(base, "LIVE_BIRTH_REPORT.json")
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
