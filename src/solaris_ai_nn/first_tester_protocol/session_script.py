"""First tester session script -- the ordered, fixture-first session steps.

:class:`FirstTesterSessionScript` builds the ordered session script (phases A-L). It is
fixture-first: the fixture demo precedes any live-read-only step, live-read-only is marked
optional and governance-gated, and stop conditions appear before every risky phase. The
script contains no upload/publish/release commands and never tells the tester to start a
feeder from Solaris.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


class SessionStepStatus:
    REQUIRED = "required"
    OPTIONAL = "optional"
    MANUAL = "manual"

    ALL = (REQUIRED, OPTIONAL, MANUAL)


class SessionPhase:
    PREPARATION = "A. Preparation"
    INSTALL = "B. Install"
    DOCTOR = "C. Doctor"
    FIXTURE_DEMO = "D. Fixture Demo"
    STATIC_CONSOLE = "E. Static Console"
    FEEDBACK_INIT = "F. Feedback Init"
    LIVE_INIT = "G. Optional Live-Read-Only Init"
    LIVE_SAMPLES = "H. Optional Live-Read-Only Sample Validation"
    LIVE_RUN = "I. Optional Live-Read-Only Run"
    BUNDLE = "J. Bundle Generation"
    FEEDBACK_COMPLETE = "K. Feedback Completion"
    HANDOFF = "L. Post-Test Handoff"

    ALL = (PREPARATION, INSTALL, DOCTOR, FIXTURE_DEMO, STATIC_CONSOLE,
           FEEDBACK_INIT, LIVE_INIT, LIVE_SAMPLES, LIVE_RUN, BUNDLE,
           FEEDBACK_COMPLETE, HANDOFF)


@dataclass
class SessionStep:
    phase: str
    status: str
    text: str = ""
    command: str = ""
    stop_note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"phase": self.phase, "status": self.status, "text": self.text,
                "command": self.command, "stop_note": self.stop_note}


def _default_steps() -> List[SessionStep]:
    S = SessionStep
    P = SessionPhase
    R, O, M = (SessionStepStatus.REQUIRED, SessionStepStatus.OPTIONAL,
               SessionStepStatus.MANUAL)
    return [
        # A. Preparation.
        S(P.PREPARATION, R, text="read the release notes "
          "(TESTER_RELEASE_NOTES.md)"),
        S(P.PREPARATION, R, text="read the safety boundaries "
          "(TESTER_SAFETY_BOUNDARIES.md)"),
        S(P.PREPARATION, R, text="read the known issues "
          "(TESTER_KNOWN_ISSUES.md)"),
        S(P.PREPARATION, R, text="confirm you understand this is a local "
          "tester RC only -- not a public release and not a product launch"),
        S(P.PREPARATION, R, text="confirm you will not provide secrets, "
          "tokens, credentials, or private data"),
        S(P.PREPARATION, R, text="confirm you will not interpret any report as "
          "evidence of consciousness, life, or agency",
          stop_note="STOP if any required doc claims consciousness/life/"
          "agency; preserve it and report it."),
        # B. Install.
        S(P.INSTALL, R, command="python -m venv .venv"),
        S(P.INSTALL, M, text="Windows: activate with "
          "`.venv\\Scripts\\Activate.ps1`; Unix/macOS: "
          "`source .venv/bin/activate`"),
        S(P.INSTALL, R, command="pip install -e ."),
        # C. Doctor.
        S(P.DOCTOR, R, command="python -m solaris_ai_nn doctor",
          stop_note="STOP the session if doctor is blocked or its output is "
          "unreadable; do not work around a doctor blocker."),
        # D. Fixture demo.
        S(P.FIXTURE_DEMO, R,
          command="python -m solaris_ai_nn tester-demo "
          "--state-dir .solaris_ai_nn_tester --profile fixture_tester_v0",
          stop_note="The fixture demo must succeed before any live-read-only "
          "step. STOP the session if it fails without a clear report."),
        # E. Static console.
        S(P.STATIC_CONSOLE, R,
          command="python -m solaris_ai_nn tester-console "
          "--state-dir .solaris_ai_nn_live "
          "--tester-state-dir .solaris_ai_nn_tester "
          "--console-dir .solaris_ai_nn_tester/console"),
        S(P.STATIC_CONSOLE, M, text="open "
          "`.solaris_ai_nn_tester/console/INDEX.md` (read-only)"),
        S(P.STATIC_CONSOLE, M, text="optionally open "
          "`.solaris_ai_nn_tester/console/INDEX.html` yourself in a browser "
          "you open manually",
          stop_note="STOP if the console fails to show blockers/warnings or "
          "hides quarantine or membrane bypass."),
        # F. Feedback init.
        S(P.FEEDBACK_INIT, R,
          command="python -m solaris_ai_nn tester-feedback-init "
          "--tester-state-dir .solaris_ai_nn_tester"),
        # G. Optional live-read-only init.
        S(P.LIVE_INIT, O,
          command="python -m solaris_ai_nn tester-live-init "
          "--state-dir .solaris_ai_nn_live "
          "--tester-state-dir .solaris_ai_nn_tester/live",
          stop_note="Live-read-only is OPTIONAL and governance-gated. Review "
          "the governance template by hand first. STOP live testing if "
          "governance is missing/unclear or the feeder registry allows a "
          "forbidden source."),
        S(P.LIVE_INIT, O,
          command="python -m solaris_ai_nn tester-live-doctor "
          "--state-dir .solaris_ai_nn_live "
          "--tester-state-dir .solaris_ai_nn_tester/live"),
        S(P.LIVE_INIT, O,
          command="python -m solaris_ai_nn tester-live-samples "
          "--state-dir .solaris_ai_nn_live "
          "--tester-state-dir .solaris_ai_nn_tester/live"),
        # H. Optional sample validation.
        S(P.LIVE_SAMPLES, O, text="confirm safe samples are accepted and "
          "unsafe samples are quarantined",
          stop_note="STOP live testing if an unsafe sample is accepted as "
          "safe, or if quarantine fails."),
        # I. Optional live-read-only run.
        S(P.LIVE_RUN, O,
          command="python -m solaris_ai_nn tester-live-run "
          "--state-dir .solaris_ai_nn_live "
          "--tester-state-dir .solaris_ai_nn_tester/live "
          "--run-birth --run-membrane --run-integration --run-observation "
          "--max-events 500",
          stop_note="Only after governance is manually reviewed and approved, "
          "and only after the fixture demo passed. STOP live testing if the "
          "membrane is missing or a raw-event bypass is detected. Solaris "
          "never starts feeders."),
        S(P.LIVE_RUN, O, text="refresh the console after the live run",
          command="python -m solaris_ai_nn tester-console "
          "--state-dir .solaris_ai_nn_live "
          "--tester-state-dir .solaris_ai_nn_tester "
          "--console-dir .solaris_ai_nn_tester/console"),
        # J. Bundle generation.
        S(P.BUNDLE, R,
          command="python -m solaris_ai_nn tester-feedback-report "
          "--tester-state-dir .solaris_ai_nn_tester"),
        S(P.BUNDLE, R,
          command="python -m solaris_ai_nn tester-feedback-bundle "
          "--tester-state-dir .solaris_ai_nn_tester"),
        S(P.BUNDLE, R,
          command="python -m solaris_ai_nn tester-bundle "
          "--state-dir .solaris_ai_nn_tester"),
        S(P.BUNDLE, O,
          command="python -m solaris_ai_nn tester-live-bundle "
          "--state-dir .solaris_ai_nn_live "
          "--tester-state-dir .solaris_ai_nn_tester/live"),
        # K. Feedback completion.
        S(P.FEEDBACK_COMPLETE, R, text="complete the feedback forms with "
          "install/CLI/report confusion; feedback is local QA evidence, never "
          "training. Do not include secrets or private data."),
        # L. Post-test handoff.
        S(P.HANDOFF, R, text="review the handoff guide; review each artifact "
          "before sharing; send manually only if the developer requests it",
          stop_note="STOP and preserve artifacts if any critical stop "
          "condition occurred. Never send artifacts anywhere automatically; "
          "sharing is manual only."),
    ]


@dataclass
class FirstTesterSessionScript:
    """Builds the ordered first-tester session script."""

    steps: List[SessionStep] = field(default_factory=_default_steps)

    def build_text(self) -> str:
        lines = ["# First Tester Session Script", "",
                 "An ordered session script for the first trusted tester. "
                 "Follow the phases in order. The fixture demo (phase D) comes "
                 "before any live-read-only step. Live-read-only (phases G-I) "
                 "is **optional** and governance-gated. Stop conditions appear "
                 "before every risky phase -- stop conditions override "
                 "curiosity.", ""]
        phase = ""
        for step in self.steps:
            if step.phase != phase:
                phase = step.phase
                lines += ["", f"## {phase}", ""]
            if step.text:
                lines.append(f"- ({step.status}) {step.text}")
            if step.command:
                lines += ["", "```bash", step.command, "```"]
            if step.stop_note:
                lines += ["", f"> **Stop condition:** {step.stop_note}"]
        lines += ["", "_Local fixture-first session script. Every command is "
                  "local and read-only with respect to feeders; none send "
                  "artifacts anywhere and none create releases/tags/issues. "
                  "Solaris controls nothing; it is local-only and "
                  "non-actuating and makes no claim of consciousness/life/"
                  "agency._"]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {"steps": [s.to_dict() for s in self.steps],
                "phase_count": len(SessionPhase.ALL),
                "fixture_first": True, "live_readonly_optional": True,
                "local_only": True, "runs_session": False}

    def write(self, scripts_dir: str) -> str:
        os.makedirs(scripts_dir, exist_ok=True)
        path = os.path.join(scripts_dir, "FIRST_TESTER_SESSION_SCRIPT.md")
        text = self.build_text()
        try:
            from ..governance.compliance import ClaimGuard
            guard = ClaimGuard()
            if not guard.scan_text(text).safe:
                text = guard.rewrite(text)
        except Exception:
            pass
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        return path
