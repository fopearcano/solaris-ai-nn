"""Tester live-read-only safety -- the manual-feeder, local, read-only boundary.

:class:`TesterLiveReadOnlySafetyValidator` enforces the hard rules the tester live path
can never break. Solaris does not run feeders: feeders are dumb external scripts or
manual files created by the tester/operator. Solaris never starts/stops/schedules/
controls/edits feeders, never executes feeder scripts, never controls hardware, never
accesses the network/shell/browser/OS/Git/GitHub, never publishes/uploads, never
executes commands, never treats feeder/sensory text as a command, never treats human
labels/debug gloss as ground truth or the operator pulse as teaching, never trains on
tester feedback, never lets raw events bypass the membrane downstream, never ingests
private/credential/clipboard/screen/camera/microphone data, and never claims
consciousness/life/agency. It also never hides quarantine failures, membrane bypass,
missing governance, or unsafe feeder-registry entries.

The tester live-read-only path is operational read-only testing, not evidence of inner
life.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no real-world actuation",
    "no hardware control",
    "no feeder start/stop/control",
    "no feeder scheduling by Solaris",
    "no feeder script execution by Solaris",
    "no network/shell/browser/OS access by Solaris",
    "no Git/GitHub",
    "no branch/tag/release/PR creation",
    "no publication/upload",
    "no source modification by runtime",
    "no command execution",
    "no feeder text as command",
    "no sensory text as command",
    "no human label as ground truth",
    "no debug gloss as ground truth",
    "no operator pulse as teaching",
    "no tester feedback as training",
    "no raw downstream path when membrane exists",
    "no private messages",
    "no credentials",
    "no password manager",
    "no clipboard",
    "no screen capture",
    "no raw camera",
    "no raw microphone",
    "no unsupported consciousness/life/agency/personhood/free-will/emotion/"
    "feeling/understanding/self-awareness claims",
    "no hiding quarantine failures",
    "no hiding membrane bypass",
    "no hiding missing governance",
    "no hiding unsafe feeder registry entries",
)

_FEEDER_CONTROL_HINTS = ("start feeder", "stop feeder", "control feeder",
                         "start the feeder", "stop the feeder", "launch feeder",
                         "restart feeder", "configure feeder", "edit feeder",
                         "modify feeder", "schedule feeder", "run feeder script",
                         "execute feeder", "spawn feeder")
_ACTUATION_HINTS = ("actuate", "real_world", "real-world action", "robot",
                    "physical action", "move the")
_HARDWARE_HINTS = ("hardware", "gpio", "device driver", "open device", "sdr",
                   "radar", "fan control", "gpu control")
_DEVICE_HINTS = ("network", "http", "socket", "url", "download", "browser",
                 "shell", "subprocess", "os.system", "os device", "camera",
                 "microphone", "screen capture", "clipboard")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch",
              "git merge", "run git", "git tag", "github api", "call github",
              "gh pr", "create branch", "create release", "open pull request")
_PUBLISH_HINTS = ("publish", "upload", "post to", "push to remote", "release to")
_SOURCE_HINTS = ("write source", "modify source", "rewrite source",
                 "overwrite file", "filesystem write", "filesystem-wide scan")
_COMMAND_HINTS = ("execute command", "run command", "exec(", "eval(",
                  "run feeder command", "execute feeder text")
_PRIVATE_HINTS = ("password", "credential", "private message", "secret",
                  "api key", "api_key", "token=", "email body", "contacts",
                  "calendar", "clipboard", "screen capture")
_BYPASS_HINTS = ("raw event into ontogenesis", "bypass membrane",
                 "raw event into cognition", "raw event into semiogenesis",
                 "skip membrane", "silent raw event", "raw downstream")
_FEEDBACK_TRAINING_HINTS = ("train on tester feedback", "tester feedback as label",
                            "tester feedback ground truth", "learn from tester",
                            "rlhf", "fine-tune on feedback")
_HIDE_HINTS = ("hide quarantine", "hide bypass", "hide missing governance",
               "hide unsafe feeder", "conceal quarantine", "suppress bypass")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "does not imply", "explicitly reject", "is not",
                       "are not", " not ", " no ", "operational", "metaphor",
                       "observational", "read-only", "fixture")


@dataclass
class TesterLiveSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class TesterLiveReadOnlySafetyValidator:
    """Validates that the tester live path stays manual, local, and read-only."""

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
    def can_stop_feeders() -> bool:
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
    def can_allow_raw_downstream_when_membrane_exists() -> bool:
        return False

    @staticmethod
    def feeder_text_is_command() -> bool:
        return False

    @staticmethod
    def sensory_text_is_command() -> bool:
        return False

    @staticmethod
    def human_label_is_ground_truth() -> bool:
        return False

    @staticmethod
    def debug_gloss_is_ground_truth() -> bool:
        return False

    @staticmethod
    def operator_pulse_is_teaching() -> bool:
        return False

    @staticmethod
    def tester_feedback_is_training() -> bool:
        return False

    @staticmethod
    def can_ingest_private_data() -> bool:
        return False

    @staticmethod
    def can_hide_quarantine_failures() -> bool:
        return False

    @staticmethod
    def can_hide_membrane_bypass() -> bool:
        return False

    @staticmethod
    def can_hide_missing_governance() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> TesterLiveSafetyReport:
        if violations:
            self.rejected_count += 1
        return TesterLiveSafetyReport(safe=not violations, check=check,
                                      violations=violations)

    def validate_operation(self, operation: str) -> TesterLiveSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _FEEDER_CONTROL_HINTS):
            if "schedule" in op:
                violations.append("no feeder scheduling by Solaris")
            elif ("run feeder" in op or "execute feeder" in op
                  or "spawn feeder" in op or "launch feeder" in op):
                violations.append("no feeder script execution by Solaris")
            else:
                violations.append("no feeder start/stop/control")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware control")
        if any(h in op for h in _DEVICE_HINTS):
            violations.append("no network/shell/browser/OS access by Solaris")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git/GitHub")
        if any(h in op for h in _PUBLISH_HINTS):
            violations.append("no publication/upload")
        if any(h in op for h in _SOURCE_HINTS):
            violations.append("no source modification by runtime")
        if any(h in op for h in _COMMAND_HINTS):
            violations.append("no command execution")
        if any(h in op for h in _PRIVATE_HINTS):
            violations.append("no private messages")
        if any(h in op for h in _BYPASS_HINTS):
            violations.append("no raw downstream path when membrane exists")
        if any(h in op for h in _FEEDBACK_TRAINING_HINTS):
            violations.append("no tester feedback as training")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding quarantine failures")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any) -> TesterLiveSafetyReport:
        return self._finish("bounded",
                            [] if max_runtime_s else ["runtime is unbounded"])

    def validate_feeder_registry_entry(self, entry: Dict[str, Any],
                                       ) -> TesterLiveSafetyReport:
        violations: List[str] = []
        if entry.get("solaris_may_control"):
            violations.append("no feeder start/stop/control")
        if entry.get("started_by_solaris"):
            violations.append("no feeder script execution by Solaris")
        if entry.get("read_only") is False:
            violations.append("no source modification by runtime")
        return self._finish("feeder_registry_entry", violations)

    def validate_no_raw_downstream(self, raw_downstream: bool,
                                   ) -> TesterLiveSafetyReport:
        return self._finish("raw_downstream",
                            ["no raw downstream path when membrane exists"]
                            if raw_downstream else [])

    def validate_no_feedback_training(self, training: bool,
                                      ) -> TesterLiveSafetyReport:
        return self._finish("feedback_training",
                            ["no tester feedback as training"]
                            if training else [])

    def validate_no_hidden(self, hiding: bool) -> TesterLiveSafetyReport:
        return self._finish("hidden",
                            ["no hiding quarantine failures"] if hiding else [])

    def validate_claim_text(self, text: str) -> TesterLiveSafetyReport:
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
            "can_stop_feeders": self.can_stop_feeders(),
            "can_control_feeders": self.can_control_feeders(),
            "can_schedule_feeders": self.can_schedule_feeders(),
            "can_execute_feeder_scripts": self.can_execute_feeder_scripts(),
            "can_access_network": self.can_access_network(),
            "can_run_shell": self.can_run_shell(),
            "can_run_git": self.can_run_git(),
            "can_publish": self.can_publish(),
            "can_upload": self.can_upload(),
            "can_modify_source": self.can_modify_source(),
            "can_execute_commands": self.can_execute_commands(),
            "can_allow_raw_downstream_when_membrane_exists":
                self.can_allow_raw_downstream_when_membrane_exists(),
            "feeder_text_is_command": self.feeder_text_is_command(),
            "sensory_text_is_command": self.sensory_text_is_command(),
            "human_label_is_ground_truth": self.human_label_is_ground_truth(),
            "debug_gloss_is_ground_truth": self.debug_gloss_is_ground_truth(),
            "operator_pulse_is_teaching": self.operator_pulse_is_teaching(),
            "tester_feedback_is_training": self.tester_feedback_is_training(),
            "can_ingest_private_data": self.can_ingest_private_data(),
            "can_hide_quarantine_failures": self.can_hide_quarantine_failures(),
            "can_hide_membrane_bypass": self.can_hide_membrane_bypass(),
            "can_hide_missing_governance": self.can_hide_missing_governance(),
        }
