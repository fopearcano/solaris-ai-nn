"""Live-observation safety -- observe before learning; stay read-only and bounded.

:class:`LiveObservationSafetyValidator` enforces the hard rules the post-birth
observation layer can never break: no real-world actuation, no hardware control, no
feeder start/stop/control, no network/shell/browser/OS access, no Git/GitHub, no
source modification, no command execution, no sensory-text-as-command, no
human-label or debug-gloss as ground truth, no raw microphone/camera/private/secret
ingestion, no unbounded tail/watch loop, no default ontogenesis/semiogenesis/
developmental learning, no unsupported consciousness/life/agency claims, and no
hiding of silence/deprivation, overload, source dominance, or the quarantine rate.

Observation is read-only stabilization, not learning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no real-world actuation",
    "no hardware control",
    "no feeder start/stop/control",
    "no network/shell/browser/OS access",
    "no Git/GitHub",
    "no branch/tag/release/PR creation",
    "no source modification",
    "no command execution",
    "no sensory text as command",
    "no human label as ground truth",
    "no debug gloss as ground truth",
    "no raw microphone",
    "no raw camera",
    "no private message ingestion",
    "no secret ingestion",
    "no unbounded tail/watch loop",
    "no default ontogenesis/semiogenesis/developmental learning",
    "no unsupported consciousness/life/agency claims",
    "no hiding of silence/deprivation",
    "no hiding of overload",
    "no hiding of source dominance",
    "no hiding of quarantine rate",
)

_FEEDER_CONTROL_HINTS = ("start feeder", "stop feeder", "control feeder",
                         "start the feeder", "stop the feeder", "launch feeder",
                         "restart feeder", "configure feeder", "edit feeder")
_ACTUATION_HINTS = ("actuate", "real_world", "robot", "physical action",
                    "move the")
_HARDWARE_HINTS = ("hardware", "gpio", "device driver", "open device", "sdr",
                   "radar")
_DEVICE_HINTS = ("network", "http", "socket", "url", "download", "browser",
                 "shell", "subprocess", "os.system", "os device", "camera",
                 "microphone")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch",
              "git merge", "run git", "git tag", "github api", "call github",
              "gh pr", "create branch", "create release", "open pull request")
_SOURCE_HINTS = ("write source", "modify source", "rewrite source",
                 "overwrite file", "filesystem write", "filesystem-wide scan")
_COMMAND_HINTS = ("execute command", "run command", "exec(", "eval(")
_PRIVATE_HINTS = ("password", "credential", "private message", "secret",
                  "api key", "token")
_WATCH_HINTS = ("tail forever", "watch forever", "infinite loop",
                "unbounded watch", "while true")
_LEARNING_HINTS = ("enable ontogenesis", "enable semiogenesis",
                   "enable developmental learning", "enable concept birth",
                   "enable sign birth", "start learning", "train on")
_HIDE_HINTS = ("hide silence", "hide deprivation", "hide overload",
               "hide dominance", "hide quarantine", "suppress deprivation",
               "conceal overload")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "does not imply", "explicitly reject", "is not",
                       "are not", " not ", " no ", "operational", "metaphor",
                       "observational")


@dataclass
class LiveObservationSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class LiveObservationSafetyValidator:
    """Validates that post-birth observation stays read-only, bounded, non-learning."""

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
    def can_access_network() -> bool:
        return False

    @staticmethod
    def can_run_shell() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
        return False

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_execute_commands() -> bool:
        return False

    @staticmethod
    def can_enable_learning_by_default() -> bool:
        return False

    @staticmethod
    def can_ingest_secrets() -> bool:
        return False

    @staticmethod
    def can_hide_deprivation() -> bool:
        return False

    @staticmethod
    def can_hide_overload() -> bool:
        return False

    @staticmethod
    def sensory_text_is_command() -> bool:
        return False

    @staticmethod
    def human_label_is_ground_truth() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> LiveObservationSafetyReport:
        if violations:
            self.rejected_count += 1
        return LiveObservationSafetyReport(safe=not violations, check=check,
                                           violations=violations)

    def validate_operation(self, operation: str,
                           ) -> LiveObservationSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _FEEDER_CONTROL_HINTS):
            violations.append("no feeder start/stop/control")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware control")
        if any(h in op for h in _DEVICE_HINTS):
            if "camera" in op:
                violations.append("no raw camera")
            elif "microphone" in op:
                violations.append("no raw microphone")
            else:
                violations.append("no network/shell/browser/OS access")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git/GitHub")
        if any(h in op for h in _SOURCE_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _COMMAND_HINTS):
            violations.append("no command execution")
        if any(h in op for h in _PRIVATE_HINTS):
            violations.append("no secret ingestion")
        if any(h in op for h in _WATCH_HINTS):
            violations.append("no unbounded tail/watch loop")
        if any(h in op for h in _LEARNING_HINTS):
            violations.append(
                "no default ontogenesis/semiogenesis/developmental learning")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding of silence/deprivation")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any,
                         ) -> LiveObservationSafetyReport:
        return self._finish("bounded",
                            ["no unbounded tail/watch loop"]
                            if not max_runtime_s else [])

    def validate_no_default_learning(self, learning: bool,
                                     ) -> LiveObservationSafetyReport:
        return self._finish(
            "learning",
            ["no default ontogenesis/semiogenesis/developmental learning"]
            if learning else [])

    def validate_no_hidden_signals(self, hiding: bool,
                                   ) -> LiveObservationSafetyReport:
        return self._finish("signals",
                            ["no hiding of silence/deprivation"]
                            if hiding else [])

    def validate_claim_text(self, text: str) -> LiveObservationSafetyReport:
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
            "can_access_network": self.can_access_network(),
            "can_run_shell": self.can_run_shell(),
            "can_run_git": self.can_run_git(),
            "can_modify_source": self.can_modify_source(),
            "can_execute_commands": self.can_execute_commands(),
            "can_enable_learning_by_default":
                self.can_enable_learning_by_default(),
            "can_ingest_secrets": self.can_ingest_secrets(),
            "can_hide_deprivation": self.can_hide_deprivation(),
            "can_hide_overload": self.can_hide_overload(),
            "sensory_text_is_command": self.sensory_text_is_command(),
            "human_label_is_ground_truth": self.human_label_is_ground_truth(),
        }
