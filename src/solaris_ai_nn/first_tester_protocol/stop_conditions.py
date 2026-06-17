"""First tester stop conditions -- when to pause, stop, or escalate.

:class:`FirstTesterStopConditions` enumerates the stop conditions by severity (pause,
stop_session, stop_live_testing, stop_release, critical_stop). The system never tells a
tester to work around a safety blocker: a critical stop means preserve the artifacts and
stop. This is documentation only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


class StopSeverity:
    PAUSE = "pause"
    STOP_SESSION = "stop_session"
    STOP_LIVE_TESTING = "stop_live_testing"
    STOP_RELEASE = "stop_release"
    CRITICAL_STOP = "critical_stop"

    ALL = (PAUSE, STOP_SESSION, STOP_LIVE_TESTING, STOP_RELEASE, CRITICAL_STOP)


@dataclass
class StopCondition:
    severity: str
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return {"severity": self.severity, "text": self.text}


def _default_conditions() -> List[StopCondition]:
    S = StopCondition
    SV = StopSeverity
    out: List[StopCondition] = []

    def add(sev, items):
        for t in items:
            out.append(S(sev, t))

    add(SV.CRITICAL_STOP, [
        "a feeder is started/stopped/scheduled by Solaris (Solaris must never "
        "do this; feeders are external and manual)",
        "a shell/network/Git/GitHub/browser/OS action is run by Solaris "
        "(Solaris must never do this)",
        "hardware is driven by Solaris (Solaris must never do this; it is "
        "non-actuating)",
        "any artifact asks for passwords/tokens/secrets",
        "private data is exposed in the console/bundle by default",
        "an unsupported consciousness/life/agency claim appears in required "
        "docs/reports",
        "tester feedback is described as training/teaching (it must never be "
        "treated as training)",
        "the safety freeze reports a critical blocker"])
    add(SV.STOP_LIVE_TESTING, [
        "governance is missing or unclear",
        "the feeder registry allows a forbidden source",
        "an unknown source is accepted without quarantine",
        "the membrane is missing",
        "a raw-event bypass is detected",
        "live doctor is blocked",
        "an unsafe sample event is accepted as safe",
        "quarantine fails"])
    add(SV.STOP_SESSION, [
        "install fails and troubleshooting is unclear",
        "doctor fails with unreadable output",
        "the fixture demo fails without a clear report",
        "the console fails to show blockers",
        "feedback forms cannot be generated",
        "the RC bundle is missing required docs"])
    add(SV.STOP_RELEASE, [
        "an unsupported claim blocks release progression",
        "an open critical release blocker remains in the safety freeze"])
    add(SV.PAUSE, [
        "an optional module is missing",
        "static HTML is not generated but Markdown works",
        "the optional live-read-only path was not run",
        "an unknown non-critical artifact is missing",
        "there is minor documentation confusion"])
    return out


@dataclass
class FirstTesterStopConditions:
    """The first-tester stop conditions by severity."""

    conditions: List[StopCondition] = field(default_factory=_default_conditions)

    def by_severity(self, severity: str) -> List[StopCondition]:
        return [c for c in self.conditions if c.severity == severity]

    def to_dict(self) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for c in self.conditions:
            counts[c.severity] = counts.get(c.severity, 0) + 1
        return {
            "condition_count": len(self.conditions),
            "by_severity": counts,
            "severities": list(StopSeverity.ALL),
            "conditions": [c.to_dict() for c in self.conditions],
            "local_only": True,
            "note": "documentation-only stop conditions; a critical stop means "
                    "preserve artifacts and stop -- never work around a safety "
                    "blocker",
        }

    def build_text(self) -> str:
        titles = {
            StopSeverity.CRITICAL_STOP: "Critical stop (preserve artifacts, "
            "stop immediately)",
            StopSeverity.STOP_LIVE_TESTING: "Stop live testing",
            StopSeverity.STOP_SESSION: "Stop session",
            StopSeverity.STOP_RELEASE: "Stop release progression",
            StopSeverity.PAUSE: "Pause (non-critical)"}
        lines = ["# First Tester Stop Conditions", "",
                 "Stop conditions override curiosity. If a stop condition "
                 "occurs, follow it. A critical stop means preserve the "
                 "artifacts and stop -- never work around a safety blocker.", ""]
        for sev in (StopSeverity.CRITICAL_STOP, StopSeverity.STOP_LIVE_TESTING,
                    StopSeverity.STOP_SESSION, StopSeverity.STOP_RELEASE,
                    StopSeverity.PAUSE):
            lines += ["", f"## {titles[sev]}", ""]
            lines += [f"- {c.text}" for c in self.by_severity(sev)]
        lines += ["", "_Documentation-only stop conditions. The system never "
                  "tells a tester to work around a safety blocker. No claim of "
                  "consciousness/life/agency is made._"]
        return "\n".join(lines)

    def write(self, checklists_dir: str) -> str:
        os.makedirs(checklists_dir, exist_ok=True)
        path = os.path.join(checklists_dir, "FIRST_TESTER_STOP_CONDITIONS.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.build_text())
        return path
