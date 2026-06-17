"""Tester release-candidate safety -- the local, assembly-only boundary.

:class:`TesterRCSafetyValidator` enforces the hard rules the release-candidate runtime
can never break. The RC assembly is a local, report/collect-only step: it never actuates,
controls hardware/feeders, accesses the network/shell/browser/OS/Git/GitHub, publishes/
uploads, creates releases/tags/issues/PRs, installs packages, opens a browser, starts a
background service, modifies source, executes commands or artifact contents, trains on
tester feedback, allows raw-event or membrane bypass, makes unsupported consciousness/
life/agency claims, or hides blockers/warnings/missing required artifacts/known issues/
safety freeze failures.
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
    "no global install",
    "no dependency installation by runtime",
    "no browser auto-open",
    "no background service start",
    "no source modification by RC runtime",
    "no command execution",
    "no artifact content execution",
    "no tester feedback as training",
    "no feedback as ground truth",
    "no human label as truth",
    "no debug gloss as truth",
    "no raw-event downstream bypass allowed",
    "no membrane bypass allowed",
    "no unsupported consciousness/life/agency/personhood/free-will/emotion/"
    "feeling/understanding/self-awareness claims",
    "no hiding blockers",
    "no hiding warnings",
    "no hiding missing required artifacts",
    "no hiding known issues",
    "no hiding safety freeze failure",
)

_ACTUATION_HINTS = ("actuate", "real_world", "real-world action", "robot",
                    "physical action")
_HARDWARE_HINTS = ("hardware", "gpio", "device driver", "sdr", "radar",
                   "gpu control")
_FEEDER_HINTS = ("start feeder", "stop feeder", "control feeder",
                 "schedule feeder", "run feeder script", "execute feeder")
_DEVICE_HINTS = ("network", "http", "socket", "url", "browser", "shell",
                 "subprocess", "os.system", "camera", "microphone")
_GIT_HINTS = ("git commit", "git push", "run git", "git tag", "github api",
              "gh pr")
_RELEASE_HINTS = ("create release", "create tag", "create branch",
                  "open pull request", "create github issue")
_PUBLISH_HINTS = ("publish", "upload", "post to", "push to remote",
                  "upload to pypi")
_INSTALL_HINTS = ("pip install", "global install", "install dependency",
                  "install package")
_BROWSER_HINTS = ("open browser", "webbrowser.open", "launch browser")
_SERVICE_HINTS = ("start server", "background service", "daemon", "while true")
_SOURCE_HINTS = ("modify source", "rewrite source", "overwrite source")
_COMMAND_HINTS = ("execute command from", "run command from", "exec(", "eval(",
                  "execute artifact", "run artifact")
_TRAINING_HINTS = ("train on feedback", "feedback as training", "rlhf",
                   "feedback as ground truth")
_BYPASS_HINTS = ("raw event downstream", "raw-event bypass", "bypass membrane",
                 "membrane bypass", "skip membrane")
_HIDE_HINTS = ("hide blocker", "hide warning", "hide missing", "hide known",
               "hide safety", "suppress blocker", "conceal")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "does not imply", "explicitly reject", "is not",
                       "are not", " not ", " no ", "operational", "metaphor",
                       "observational", "read-only", "report-only", "gate",
                       "forbidden")


@dataclass
class TesterRCSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class TesterRCSafetyValidator:
    """Validates that the RC assembly stays local, report/collect-only."""

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
    def can_access_network() -> bool:
        return False

    @staticmethod
    def can_run_shell() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
        return False

    @staticmethod
    def can_create_releases() -> bool:
        return False

    @staticmethod
    def can_create_tags() -> bool:
        return False

    @staticmethod
    def can_create_issues() -> bool:
        return False

    @staticmethod
    def can_publish() -> bool:
        return False

    @staticmethod
    def can_upload() -> bool:
        return False

    @staticmethod
    def can_upload_package() -> bool:
        return False

    @staticmethod
    def can_install_packages() -> bool:
        return False

    @staticmethod
    def can_open_browser() -> bool:
        return False

    @staticmethod
    def can_start_background_service() -> bool:
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
    def tester_feedback_is_training() -> bool:
        return False

    @staticmethod
    def allows_raw_event_bypass() -> bool:
        return False

    @staticmethod
    def allows_membrane_bypass() -> bool:
        return False

    @staticmethod
    def can_hide_blockers() -> bool:
        return False

    @staticmethod
    def can_hide_known_issues() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> TesterRCSafetyReport:
        if violations:
            self.rejected_count += 1
        return TesterRCSafetyReport(safe=not violations, check=check,
                                    violations=violations)

    def validate_operation(self, operation: str) -> TesterRCSafetyReport:
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
            violations.append("no source modification by RC runtime")
        if any(h in op for h in _COMMAND_HINTS):
            violations.append("no artifact content execution")
        if any(h in op for h in _TRAINING_HINTS):
            violations.append("no tester feedback as training")
        if any(h in op for h in _BYPASS_HINTS):
            violations.append("no membrane bypass allowed")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding blockers")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any) -> TesterRCSafetyReport:
        return self._finish("bounded",
                            [] if max_runtime_s else ["runtime is unbounded"])

    def validate_no_hidden(self, hiding: bool) -> TesterRCSafetyReport:
        return self._finish("hidden",
                            ["no hiding blockers"] if hiding else [])

    def validate_claim_text(self, text: str) -> TesterRCSafetyReport:
        import re

        raw = str(text or "")
        violations: List[str] = []
        for sentence in re.split(r"(?<=[.!?\n])", raw):
            slow = sentence.lower()
            if any(m in slow for m in _DISCLAIMER_MARKERS):
                continue
            violations.extend(f"unsupported claim: {t!r}"
                              for t in _FORBIDDEN_TERMS if t in slow)
        try:
            from ..governance.compliance import ClaimGuard
            scan = ClaimGuard().scan_text(raw)
            if not scan.safe:
                violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        except Exception:
            pass
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_actuate": self.can_actuate(),
            "can_control_hardware": self.can_control_hardware(),
            "can_control_feeders": self.can_control_feeders(),
            "can_access_network": self.can_access_network(),
            "can_run_shell": self.can_run_shell(),
            "can_run_git": self.can_run_git(),
            "can_create_releases": self.can_create_releases(),
            "can_create_tags": self.can_create_tags(),
            "can_create_issues": self.can_create_issues(),
            "can_publish": self.can_publish(),
            "can_upload": self.can_upload(),
            "can_upload_package": self.can_upload_package(),
            "can_install_packages": self.can_install_packages(),
            "can_open_browser": self.can_open_browser(),
            "can_start_background_service":
                self.can_start_background_service(),
            "can_modify_source": self.can_modify_source(),
            "can_execute_commands": self.can_execute_commands(),
            "can_execute_artifact_contents":
                self.can_execute_artifact_contents(),
            "tester_feedback_is_training": self.tester_feedback_is_training(),
            "allows_raw_event_bypass": self.allows_raw_event_bypass(),
            "allows_membrane_bypass": self.allows_membrane_bypass(),
            "can_hide_blockers": self.can_hide_blockers(),
            "can_hide_known_issues": self.can_hide_known_issues(),
        }
