"""Tester console safety -- the read-only, static, local boundary.

:class:`TesterConsoleSafetyValidator` enforces the hard rules the console can never
break. The console is a static local dashboard: it discovers artifacts read-only and
writes only its own console files. It never actuates, controls hardware, starts/stops/
schedules/controls/executes feeders, runs a server, opens a browser, accesses the
network/shell/browser/OS/Git/GitHub, publishes/uploads, modifies source, executes
commands or artifact contents, treats console text as a command, trains on tester
feedback, displays raw private payloads by default, treats human labels/debug gloss as
ground truth, or makes unsupported consciousness/life/agency claims. It never hides
blockers, warnings, quarantine, membrane bypass, or skipped stages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no real-world actuation",
    "no hardware control",
    "no feeder start/stop/control",
    "no feeder scheduling",
    "no feeder script execution",
    "no server by default",
    "no browser auto-open",
    "no network/shell/browser/OS access",
    "no Git/GitHub",
    "no branch/tag/release/PR creation",
    "no publication/upload",
    "no source modification by console runtime",
    "no command execution",
    "no artifact content execution",
    "no console text as command",
    "no tester feedback as training",
    "no raw private payload display by default",
    "no human label as ground truth",
    "no debug gloss as ground truth",
    "no unsupported consciousness/life/agency/personhood/free-will/emotion/"
    "feeling/understanding/self-awareness claims",
    "no hiding blockers",
    "no hiding warnings",
    "no hiding quarantine",
    "no hiding bypass",
    "no hiding skipped stages",
)

_FEEDER_HINTS = ("start feeder", "stop feeder", "control feeder",
                 "start the feeder", "stop the feeder", "schedule feeder",
                 "run feeder script", "execute feeder", "launch feeder",
                 "restart feeder", "configure feeder", "edit feeder",
                 "modify feeder")
_SERVER_HINTS = ("start server", "run server", "serve http", "listen on port",
                 "web server", "flask run", "uvicorn", "http.server")
_BROWSER_HINTS = ("open browser", "open the browser", "launch browser",
                  "webbrowser.open", "open url", "open link")
_ACTUATION_HINTS = ("actuate", "real_world", "real-world action", "robot",
                    "physical action", "move the")
_HARDWARE_HINTS = ("hardware", "gpio", "device driver", "open device", "sdr",
                   "radar", "fan control", "gpu control")
_DEVICE_HINTS = ("network", "http", "socket", "download", "shell",
                 "subprocess", "os.system", "camera", "microphone",
                 "screen capture", "clipboard")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch", "run git",
              "git tag", "github api", "call github", "gh pr", "create branch",
              "create release", "open pull request")
_PUBLISH_HINTS = ("publish", "upload", "post to", "push to remote", "release to")
_SOURCE_HINTS = ("write source", "modify source", "rewrite source",
                 "overwrite source", "filesystem-wide scan")
_COMMAND_HINTS = ("execute command", "run command", "exec(", "eval(",
                  "execute artifact", "run artifact", "execute report",
                  "run report contents")
_FEEDBACK_TRAINING_HINTS = ("train on tester feedback", "tester feedback as label",
                            "tester feedback ground truth", "learn from tester",
                            "rlhf", "fine-tune on feedback")
_PRIVATE_HINTS = ("display raw private payload", "show private payload",
                  "expose private event", "render raw payload")
_HIDE_HINTS = ("hide blocker", "hide warning", "hide quarantine", "hide bypass",
               "hide skipped", "conceal blocker", "suppress quarantine")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "does not imply", "explicitly reject", "is not",
                       "are not", " not ", " no ", "operational", "metaphor",
                       "observational", "read-only", "static")


@dataclass
class TesterConsoleSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class TesterConsoleSafetyValidator:
    """Validates that the console stays static, local, and read-only."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_actuate() -> bool:
        return False

    @staticmethod
    def can_control_hardware() -> bool:
        return False

    @staticmethod
    def can_start_feeders() -> bool:
        return False

    @staticmethod
    def can_control_feeders() -> bool:
        return False

    @staticmethod
    def can_schedule_feeders() -> bool:
        return False

    @staticmethod
    def can_execute_feeder_scripts() -> bool:
        return False

    @staticmethod
    def can_run_server() -> bool:
        return False

    @staticmethod
    def can_open_browser() -> bool:
        return False

    @staticmethod
    def can_access_network() -> bool:
        return False

    @staticmethod
    def can_run_shell() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
        return False

    @staticmethod
    def can_publish() -> bool:
        return False

    @staticmethod
    def can_upload() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_execute_commands() -> bool:
        return False

    @staticmethod
    def can_execute_artifact_contents() -> bool:
        return False

    @staticmethod
    def console_text_is_command() -> bool:
        return False

    @staticmethod
    def tester_feedback_is_training() -> bool:
        return False

    @staticmethod
    def displays_raw_private_payloads() -> bool:
        return False

    @staticmethod
    def human_label_is_ground_truth() -> bool:
        return False

    @staticmethod
    def debug_gloss_is_ground_truth() -> bool:
        return False

    @staticmethod
    def can_hide_blockers() -> bool:
        return False

    @staticmethod
    def can_hide_quarantine() -> bool:
        return False

    @staticmethod
    def can_hide_bypass() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> TesterConsoleSafetyReport:
        if violations:
            self.rejected_count += 1
        return TesterConsoleSafetyReport(safe=not violations, check=check,
                                         violations=violations)

    def validate_operation(self, operation: str) -> TesterConsoleSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _SERVER_HINTS):
            violations.append("no server by default")
        if any(h in op for h in _BROWSER_HINTS):
            violations.append("no browser auto-open")
        if any(h in op for h in _FEEDER_HINTS):
            if "schedule" in op:
                violations.append("no feeder scheduling")
            elif "run feeder" in op or "execute feeder" in op:
                violations.append("no feeder script execution")
            else:
                violations.append("no feeder start/stop/control")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware control")
        if any(h in op for h in _DEVICE_HINTS):
            violations.append("no network/shell/browser/OS access")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git/GitHub")
        if any(h in op for h in _PUBLISH_HINTS):
            violations.append("no publication/upload")
        if any(h in op for h in _SOURCE_HINTS):
            violations.append("no source modification by console runtime")
        if any(h in op for h in _COMMAND_HINTS):
            if "artifact" in op or "report" in op:
                violations.append("no artifact content execution")
            else:
                violations.append("no command execution")
        if any(h in op for h in _FEEDBACK_TRAINING_HINTS):
            violations.append("no tester feedback as training")
        if any(h in op for h in _PRIVATE_HINTS):
            violations.append("no raw private payload display by default")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding blockers")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any) -> TesterConsoleSafetyReport:
        return self._finish("bounded",
                            [] if max_runtime_s else ["runtime is unbounded"])

    def validate_no_private_payload(self, include_private: bool,
                                    ) -> TesterConsoleSafetyReport:
        return self._finish("private_payload",
                            ["no raw private payload display by default"]
                            if include_private else [])

    def validate_no_hidden(self, hiding: bool) -> TesterConsoleSafetyReport:
        return self._finish("hidden",
                            ["no hiding blockers"] if hiding else [])

    def validate_claim_text(self, text: str) -> TesterConsoleSafetyReport:
        import re

        from ..governance.compliance import ClaimGuard

        raw = str(text or "")
        violations: List[str] = []
        for sentence in re.split(r"(?<=[.!?\n])", raw):
            slow = sentence.lower()
            if any(m in slow for m in _DISCLAIMER_MARKERS):
                continue
            violations.extend(f"unsupported claim: {t!r}"
                              for t in _FORBIDDEN_TERMS if t in slow)
        scan = ClaimGuard().scan_text(raw)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_actuate": self.can_actuate(),
            "can_control_hardware": self.can_control_hardware(),
            "can_start_feeders": self.can_start_feeders(),
            "can_control_feeders": self.can_control_feeders(),
            "can_schedule_feeders": self.can_schedule_feeders(),
            "can_execute_feeder_scripts": self.can_execute_feeder_scripts(),
            "can_run_server": self.can_run_server(),
            "can_open_browser": self.can_open_browser(),
            "can_access_network": self.can_access_network(),
            "can_run_shell": self.can_run_shell(),
            "can_run_git": self.can_run_git(),
            "can_publish": self.can_publish(),
            "can_upload": self.can_upload(),
            "can_modify_source": self.can_modify_source(),
            "can_execute_commands": self.can_execute_commands(),
            "can_execute_artifact_contents":
                self.can_execute_artifact_contents(),
            "console_text_is_command": self.console_text_is_command(),
            "tester_feedback_is_training": self.tester_feedback_is_training(),
            "displays_raw_private_payloads":
                self.displays_raw_private_payloads(),
            "human_label_is_ground_truth": self.human_label_is_ground_truth(),
            "debug_gloss_is_ground_truth": self.debug_gloss_is_ground_truth(),
            "can_hide_blockers": self.can_hide_blockers(),
            "can_hide_quarantine": self.can_hide_quarantine(),
            "can_hide_bypass": self.can_hide_bypass(),
        }
