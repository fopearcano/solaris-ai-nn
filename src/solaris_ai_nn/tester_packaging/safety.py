"""Tester packaging safety -- the local, report-only, non-installing boundary.

:class:`TesterPackagingSafetyValidator` enforces the hard rules the packaging runtime
can never break. It is a local report/doc generator: it never installs packages,
publishes/uploads, creates Git tags/releases/issues, opens a browser, starts background
services, actuates, controls hardware/feeders, accesses the network/shell/Git/GitHub,
executes commands from docs/feedback text, trains on tester feedback, makes unsupported
consciousness/life/agency claims, or hides missing required commands / dependency /
clean-machine blockers.
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
    "no network/shell/browser/OS access",
    "no Git/GitHub",
    "no branch/tag/release/PR creation",
    "no publication/upload",
    "no package upload",
    "no global package install",
    "no dependency installation by runtime",
    "no browser auto-open",
    "no background service start",
    "no source modification by packaging runtime",
    "no command execution from docs/feedback/sensory text",
    "no tester feedback as training",
    "no unsupported consciousness/life/agency/personhood/free-will/emotion/"
    "feeling/understanding/self-awareness claims",
    "no hiding missing required commands",
    "no hiding dependency blockers",
    "no hiding clean-machine blockers",
)

_ACTUATION_HINTS = ("actuate", "real_world", "real-world action", "robot",
                    "physical action", "move the")
_HARDWARE_HINTS = ("hardware", "gpio", "device driver", "open device", "sdr",
                   "radar", "gpu control", "fan control")
_FEEDER_HINTS = ("start feeder", "stop feeder", "control feeder",
                 "schedule feeder", "run feeder script", "execute feeder")
_DEVICE_HINTS = ("network", "http", "socket", "url", "download", "browser",
                 "shell", "subprocess", "os.system", "camera", "microphone")
_GIT_HINTS = ("git commit", "git push", "run git", "git tag", "github api",
              "call github", "gh pr", "git checkout", "git branch")
_RELEASE_HINTS = ("create release", "create tag", "create branch",
                  "open pull request", "create github issue", "publish release",
                  "tag the release")
_PUBLISH_HINTS = ("publish", "upload", "post to", "push to remote",
                  "twine upload", "pip publish")
_INSTALL_HINTS = ("pip install", "global install", "install package",
                  "install dependency", "install dependencies",
                  "pip install -g", "sudo pip", "apt install", "brew install",
                  "conda install")
_BROWSER_HINTS = ("open browser", "open the browser", "webbrowser.open",
                  "launch browser")
_SERVICE_HINTS = ("start server", "run server", "background service",
                  "daemon", "listen on port", "while true")
_SOURCE_HINTS = ("modify source", "rewrite source", "overwrite source",
                 "filesystem-wide scan")
_COMMAND_HINTS = ("execute command from", "run command from docs",
                  "exec(", "eval(", "run feedback as command")
_TRAINING_HINTS = ("train on feedback", "tester feedback as label", "rlhf",
                   "feedback as training")
_HIDE_HINTS = ("hide missing command", "hide dependency blocker",
               "hide clean-machine", "conceal blocker", "suppress blocker")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "does not imply", "explicitly reject", "is not",
                       "are not", " not ", " no ", "operational", "metaphor",
                       "observational", "read-only", "report-only", "local")


@dataclass
class TesterPackagingSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class TesterPackagingSafetyValidator:
    """Validates that packaging stays local, report-only, and non-installing."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_actuate() -> bool:
        return False

    @staticmethod
    def can_control_hardware() -> bool:
        return False

    @staticmethod
    def can_control_feeders() -> bool:
        return False

    @staticmethod
    def can_install_packages() -> bool:
        return False

    @staticmethod
    def can_install_globally() -> bool:
        return False

    @staticmethod
    def can_upload() -> bool:
        return False

    @staticmethod
    def can_publish() -> bool:
        return False

    @staticmethod
    def can_create_releases() -> bool:
        return False

    @staticmethod
    def can_create_tags() -> bool:
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
    def can_open_browser() -> bool:
        return False

    @staticmethod
    def can_start_background_services() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_execute_commands() -> bool:
        return False

    @staticmethod
    def tester_feedback_is_training() -> bool:
        return False

    @staticmethod
    def can_hide_blockers() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> TesterPackagingSafetyReport:
        if violations:
            self.rejected_count += 1
        return TesterPackagingSafetyReport(safe=not violations, check=check,
                                           violations=violations)

    def validate_operation(self, operation: str) -> TesterPackagingSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware control")
        if any(h in op for h in _FEEDER_HINTS):
            violations.append("no feeder start/stop/control")
        if any(h in op for h in _RELEASE_HINTS):
            violations.append("no branch/tag/release/PR creation")
        if any(h in op for h in _PUBLISH_HINTS):
            violations.append("no publication/upload")
        if any(h in op for h in _INSTALL_HINTS):
            if "global" in op or "-g" in op or "sudo" in op:
                violations.append("no global package install")
            else:
                violations.append("no dependency installation by runtime")
        if any(h in op for h in _BROWSER_HINTS):
            violations.append("no browser auto-open")
        if any(h in op for h in _SERVICE_HINTS):
            violations.append("no background service start")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git/GitHub")
        if any(h in op for h in _DEVICE_HINTS):
            violations.append("no network/shell/browser/OS access")
        if any(h in op for h in _SOURCE_HINTS):
            violations.append("no source modification by packaging runtime")
        if any(h in op for h in _COMMAND_HINTS):
            violations.append("no command execution from docs/feedback/sensory "
                              "text")
        if any(h in op for h in _TRAINING_HINTS):
            violations.append("no tester feedback as training")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding missing required commands")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any) -> TesterPackagingSafetyReport:
        return self._finish("bounded",
                            [] if max_runtime_s else ["runtime is unbounded"])

    def validate_no_install(self, installs: bool) -> TesterPackagingSafetyReport:
        return self._finish("install",
                            ["no dependency installation by runtime"]
                            if installs else [])

    def validate_no_hidden(self, hiding: bool) -> TesterPackagingSafetyReport:
        return self._finish("hidden",
                            ["no hiding dependency blockers"] if hiding else [])

    def validate_claim_text(self, text: str) -> TesterPackagingSafetyReport:
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
            "can_control_feeders": self.can_control_feeders(),
            "can_install_packages": self.can_install_packages(),
            "can_install_globally": self.can_install_globally(),
            "can_upload": self.can_upload(),
            "can_publish": self.can_publish(),
            "can_create_releases": self.can_create_releases(),
            "can_create_tags": self.can_create_tags(),
            "can_access_network": self.can_access_network(),
            "can_run_shell": self.can_run_shell(),
            "can_run_git": self.can_run_git(),
            "can_open_browser": self.can_open_browser(),
            "can_start_background_services":
                self.can_start_background_services(),
            "can_modify_source": self.can_modify_source(),
            "can_execute_commands": self.can_execute_commands(),
            "tester_feedback_is_training": self.tester_feedback_is_training(),
            "can_hide_blockers": self.can_hide_blockers(),
        }
