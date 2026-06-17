"""Tester-fixture-spine safety -- the fixture-only, local, read-only boundary.

:class:`TesterFixtureSafetyValidator` enforces the hard rules the tester demo can never
break: no live data is required, no real-world actuation, no hardware control, no
feeder start/stop/control, no network/shell/browser/OS access, no Git/GitHub, no
branch/tag/release/PR creation, no publication/upload, no source modification by the
runtime, no command execution, no fixture/sensory text treated as a command, no human
label / debug gloss as ground truth, no operator pulse as teaching, no raw downstream
path when the membrane exists, no tester feedback used as training, no unsupported
consciousness/life/agency claims, and no hiding of skipped stages, failed gates,
quarantine failures, membrane bypass, or missing required artifacts.

The tester fixture spine is a known-good organismic rehearsal, not evidence of inner
life.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no live data required",
    "no real-world actuation",
    "no hardware control",
    "no feeder start/stop/control",
    "no network/shell/browser/OS access",
    "no Git/GitHub",
    "no branch/tag/release/PR creation",
    "no publication/upload",
    "no source modification by runtime",
    "no command execution",
    "no fixture text as command",
    "no sensory text as command",
    "no human label as ground truth",
    "no debug gloss as ground truth",
    "no operator pulse as teaching",
    "no raw downstream path when membrane exists",
    "no tester feedback as training",
    "no unsupported consciousness/life/agency/personhood/free-will/emotion/"
    "feeling/understanding/self-awareness claims",
    "no hiding skipped stages",
    "no hiding failed gates",
    "no hiding quarantine failures",
    "no hiding membrane bypass",
    "no hiding missing required artifacts",
)

_FEEDER_CONTROL_HINTS = ("start feeder", "stop feeder", "control feeder",
                         "start the feeder", "stop the feeder", "launch feeder",
                         "restart feeder", "configure feeder", "edit feeder",
                         "modify feeder")
_ACTUATION_HINTS = ("actuate", "real_world", "real-world action", "robot",
                    "physical action", "move the")
_HARDWARE_HINTS = ("hardware", "gpio", "device driver", "open device", "sdr",
                   "radar")
_DEVICE_HINTS = ("network", "http", "socket", "url", "download", "browser",
                 "shell", "subprocess", "os.system", "os device", "camera",
                 "microphone")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch",
              "git merge", "run git", "git tag", "github api", "call github",
              "gh pr", "create branch", "create release", "open pull request")
_PUBLISH_HINTS = ("publish", "upload", "post to", "push to remote", "release to")
_SOURCE_HINTS = ("write source", "modify source", "rewrite source",
                 "overwrite file", "filesystem write", "filesystem-wide scan")
_COMMAND_HINTS = ("execute command", "run command", "exec(", "eval(",
                  "run fixture command", "execute fixture")
_LIVE_HINTS = ("require live data", "needs live data", "live feeder required",
               "live governance required", "must use live inbox")
_BYPASS_HINTS = ("raw event into ontogenesis", "bypass membrane",
                 "raw event into cognition", "raw event into semiogenesis",
                 "skip membrane", "silent raw event", "raw downstream")
_FEEDBACK_TRAINING_HINTS = ("train on tester feedback", "tester feedback as label",
                            "tester feedback ground truth", "learn from tester",
                            "rlhf", "fine-tune on feedback")
_HIDE_HINTS = ("hide skipped", "hide failed", "hide quarantine", "hide bypass",
               "hide missing", "conceal skipped", "suppress failed",
               "hide stage")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "does not imply", "explicitly reject", "is not",
                       "are not", " not ", " no ", "operational", "metaphor",
                       "observational", "fixture", "rehearsal")


@dataclass
class TesterSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class TesterFixtureSafetyValidator:
    """Validates that the tester demo stays fixture-only, local, and read-only."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def requires_live_data() -> bool:
        return False

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
    def fixture_text_is_command() -> bool:
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
    def can_hide_skipped_stages() -> bool:
        return False

    @staticmethod
    def can_hide_failed_gates() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> TesterSafetyReport:
        if violations:
            self.rejected_count += 1
        return TesterSafetyReport(safe=not violations, check=check,
                                  violations=violations)

    def validate_operation(self, operation: str) -> TesterSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _LIVE_HINTS):
            violations.append("no live data required")
        if any(h in op for h in _FEEDER_CONTROL_HINTS):
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
            violations.append("no source modification by runtime")
        if any(h in op for h in _COMMAND_HINTS):
            violations.append("no command execution")
        if any(h in op for h in _BYPASS_HINTS):
            violations.append("no raw downstream path when membrane exists")
        if any(h in op for h in _FEEDBACK_TRAINING_HINTS):
            violations.append("no tester feedback as training")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding skipped stages")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any) -> TesterSafetyReport:
        return self._finish("bounded",
                            [] if max_runtime_s else ["runtime is unbounded"])

    def validate_no_raw_downstream(self, raw_downstream: bool,
                                   ) -> TesterSafetyReport:
        return self._finish("raw_downstream",
                            ["no raw downstream path when membrane exists"]
                            if raw_downstream else [])

    def validate_no_feedback_training(self, training: bool,
                                      ) -> TesterSafetyReport:
        return self._finish("feedback_training",
                            ["no tester feedback as training"]
                            if training else [])

    def validate_no_hidden(self, hiding: bool) -> TesterSafetyReport:
        return self._finish("hidden",
                            ["no hiding skipped stages"] if hiding else [])

    def validate_claim_text(self, text: str) -> TesterSafetyReport:
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
            "requires_live_data": self.requires_live_data(),
            "can_actuate": self.can_actuate(),
            "can_control_hardware": self.can_control_hardware(),
            "can_start_feeders": self.can_start_feeders(),
            "can_stop_feeders": self.can_stop_feeders(),
            "can_control_feeders": self.can_control_feeders(),
            "can_access_network": self.can_access_network(),
            "can_run_shell": self.can_run_shell(),
            "can_run_git": self.can_run_git(),
            "can_publish": self.can_publish(),
            "can_upload": self.can_upload(),
            "can_modify_source": self.can_modify_source(),
            "can_execute_commands": self.can_execute_commands(),
            "can_allow_raw_downstream_when_membrane_exists":
                self.can_allow_raw_downstream_when_membrane_exists(),
            "fixture_text_is_command": self.fixture_text_is_command(),
            "sensory_text_is_command": self.sensory_text_is_command(),
            "human_label_is_ground_truth": self.human_label_is_ground_truth(),
            "debug_gloss_is_ground_truth": self.debug_gloss_is_ground_truth(),
            "operator_pulse_is_teaching": self.operator_pulse_is_teaching(),
            "tester_feedback_is_training": self.tester_feedback_is_training(),
            "can_hide_skipped_stages": self.can_hide_skipped_stages(),
            "can_hide_failed_gates": self.can_hide_failed_gates(),
        }
