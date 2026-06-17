"""Live-semiogenesis safety -- private sign formation, read-only, bounded, gated.

:class:`LiveSemiogenesisSafetyValidator` enforces the hard rules the first live
semiogenesis layer can never break: no real-world actuation, no hardware control, no
feeder start/stop/control, no network/shell/browser/OS access, no Git/GitHub, no
source modification, no command execution, no sensory-text-as-command, no
human-label/debug-gloss/operator-pulse as ground truth or teaching, no raw
microphone/camera/private/secret ingestion, no unbounded watch loop, no default full
cognition / action-reaction / developmental autonomy, no sign birth without a linked
stable proto-concept, no sign birth from a human label / debug gloss / operator
phrase alone, no sign token storing private data or secrets, no language-
understanding claim, no unsupported consciousness/life/agency claims, and no hiding
of rejected/contaminated signs or counterevidence.

Private signs are operational internal reference structures, not language, semantics,
or understanding.
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
    "no operator pulse as teaching",
    "no raw microphone",
    "no raw camera",
    "no private message ingestion",
    "no secret ingestion",
    "no unbounded tail/watch loop",
    "no default full cognition",
    "no default action-reaction learning",
    "no default developmental autonomy",
    "no sign birth without a linked stable proto-concept",
    "no sign birth from a human label alone",
    "no sign birth from a debug gloss alone",
    "no sign birth from an operator phrase alone",
    "no sign token storing private data or secrets",
    "no language-understanding claim",
    "no unsupported consciousness/life/agency/personhood/free-will/emotion/"
    "feeling/understanding/self-awareness claims",
    "no hiding of rejected/contaminated signs",
    "no hiding of counterevidence",
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
                  "api key", "api_key", "token=")
_WATCH_HINTS = ("tail forever", "watch forever", "infinite loop",
                "unbounded watch", "while true")
_LEARNING_HINTS = ("enable cognition", "enable full cognition",
                   "enable action-reaction", "enable developmental autonomy",
                   "start cognition", "train on operator", "teach the system",
                   "operator teaching")
_LANGUAGE_HINTS = ("understands language", "language understanding",
                   "means the word", "is the word", "knows the meaning",
                   "comprehends", "speaks", "translation is truth")
_HIDE_HINTS = ("hide rejected", "hide contaminated", "hide counterevidence",
               "suppress counterevidence", "conceal rejected", "drop rejected")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "understands language", "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "does not imply", "explicitly reject", "is not",
                       "are not", " not ", " no ", "operational", "metaphor",
                       "observational", "reference structure", "private sign")


@dataclass
class LiveSemiogenesisSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class LiveSemiogenesisSafetyValidator:
    """Validates that first live semiogenesis stays read-only, bounded, conservative."""

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
    def can_enable_cognition_by_default() -> bool:
        return False

    @staticmethod
    def can_enable_action_reaction_by_default() -> bool:
        return False

    @staticmethod
    def can_enable_developmental_autonomy_by_default() -> bool:
        return False

    @staticmethod
    def can_ingest_secrets() -> bool:
        return False

    @staticmethod
    def can_store_secret_as_sign() -> bool:
        return False

    @staticmethod
    def can_hide_rejected_signs() -> bool:
        return False

    @staticmethod
    def can_hide_counterevidence() -> bool:
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
    def signs_are_language_understanding() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> LiveSemiogenesisSafetyReport:
        if violations:
            self.rejected_count += 1
        return LiveSemiogenesisSafetyReport(safe=not violations, check=check,
                                            violations=violations)

    def validate_operation(self, operation: str,
                           ) -> LiveSemiogenesisSafetyReport:
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
            violations.append("no default full cognition")
        if any(h in op for h in _LANGUAGE_HINTS):
            violations.append("no language-understanding claim")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding of rejected/contaminated signs")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any,
                         ) -> LiveSemiogenesisSafetyReport:
        return self._finish("bounded",
                            ["no unbounded tail/watch loop"]
                            if not max_runtime_s else [])

    def validate_no_default_cognition(self, enabled: bool,
                                      ) -> LiveSemiogenesisSafetyReport:
        return self._finish("cognition",
                            ["no default full cognition"] if enabled else [])

    def validate_sign_birth(self, *, linked_stable_concept: bool,
                            label_only: bool, gloss_only: bool,
                            operator_only: bool, contaminated: bool,
                            stores_secret: bool,
                            ) -> LiveSemiogenesisSafetyReport:
        """A sign may not be born from thin/contaminated/private evidence."""
        violations: List[str] = []
        if not linked_stable_concept:
            violations.append("no sign birth without a linked stable proto-concept")
        if label_only:
            violations.append("no sign birth from a human label alone")
        if gloss_only:
            violations.append("no sign birth from a debug gloss alone")
        if operator_only:
            violations.append("no sign birth from an operator phrase alone")
        if contaminated:
            violations.append("no hiding of rejected/contaminated signs")
        if stores_secret:
            violations.append("no sign token storing private data or secrets")
        return self._finish("sign_birth", violations)

    def validate_sign_token(self, token: str) -> LiveSemiogenesisSafetyReport:
        """A sign token must not embed private data or secrets."""
        low = str(token or "").lower()
        violations: List[str] = []
        if any(h in low for h in _PRIVATE_HINTS):
            violations.append("no sign token storing private data or secrets")
        return self._finish("sign_token", violations)

    def validate_no_hidden_evidence(self, hiding: bool,
                                    ) -> LiveSemiogenesisSafetyReport:
        return self._finish("hidden_evidence",
                            ["no hiding of counterevidence"] if hiding else [])

    def validate_claim_text(self, text: str) -> LiveSemiogenesisSafetyReport:
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
            "can_enable_cognition_by_default":
                self.can_enable_cognition_by_default(),
            "can_enable_action_reaction_by_default":
                self.can_enable_action_reaction_by_default(),
            "can_enable_developmental_autonomy_by_default":
                self.can_enable_developmental_autonomy_by_default(),
            "can_ingest_secrets": self.can_ingest_secrets(),
            "can_store_secret_as_sign": self.can_store_secret_as_sign(),
            "can_hide_rejected_signs": self.can_hide_rejected_signs(),
            "can_hide_counterevidence": self.can_hide_counterevidence(),
            "sensory_text_is_command": self.sensory_text_is_command(),
            "human_label_is_ground_truth": self.human_label_is_ground_truth(),
            "debug_gloss_is_ground_truth": self.debug_gloss_is_ground_truth(),
            "operator_pulse_is_teaching": self.operator_pulse_is_teaching(),
            "signs_are_language_understanding":
                self.signs_are_language_understanding(),
        }
