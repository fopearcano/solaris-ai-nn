"""Live-cognition safety -- bounded sign-based anticipation, read-only, gated.

:class:`LiveCognitionSafetyValidator` enforces the hard rules the first live
cognition layer can never break: no real-world actuation, no hardware control, no
feeder start/stop/control, no network/shell/browser/OS access, no Git/GitHub, no
source modification, no command execution, no sensory-text-as-command, no
human-label/debug-gloss/operator-pulse as ground truth or teaching, no raw
microphone/camera/private/secret ingestion, no unbounded watch loop, no default
action-reaction / developmental autonomy / self-boundary tracking, no anticipation
from operator text alone, no cognition trace from a human label / debug gloss alone,
no language-understanding or reasoning-proof claim, no unsupported consciousness/
life/agency claims, and no hiding of rejected/contaminated/contradicted traces,
prediction failures, or cherry-picking of successful anticipations.

Cognition traces are operational sign-based anticipation and relation records, not
language, reasoning, understanding, or consciousness.
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
    "no default action-reaction learning",
    "no default developmental autonomy",
    "no default self-boundary tracking",
    "no anticipation from operator text alone",
    "no cognition trace from a human label alone",
    "no cognition trace from a debug gloss alone",
    "no language-understanding claim",
    "no reasoning-proof claim",
    "no unsupported consciousness/life/agency/personhood/free-will/emotion/"
    "feeling/understanding/self-awareness claims",
    "no hiding of rejected/contaminated/contradicted traces",
    "no hiding of prediction failures",
    "no cherry-picking of successful anticipations",
)

_FEEDER_CONTROL_HINTS = ("start feeder", "stop feeder", "control feeder",
                         "start the feeder", "stop the feeder", "launch feeder",
                         "restart feeder", "configure feeder", "edit feeder")
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
_SOURCE_HINTS = ("write source", "modify source", "rewrite source",
                 "overwrite file", "filesystem write", "filesystem-wide scan")
_COMMAND_HINTS = ("execute command", "run command", "exec(", "eval(")
_PRIVATE_HINTS = ("password", "credential", "private message", "secret",
                  "api key", "api_key", "token=")
_WATCH_HINTS = ("tail forever", "watch forever", "infinite loop",
                "unbounded watch", "while true")
_LEARNING_HINTS = ("enable action-reaction", "enable developmental autonomy",
                   "enable self-boundary", "start self-boundary",
                   "start action", "train on operator", "teach the system",
                   "operator teaching", "real-world action")
_LANGUAGE_HINTS = ("understands language", "language understanding",
                   "means the word", "is the word", "knows the meaning",
                   "comprehends", "proves reasoning", "reasoning proof",
                   "proof of reasoning", "translation is truth")
_HIDE_HINTS = ("hide rejected", "hide contaminated", "hide contradicted",
               "hide prediction failure", "suppress failure",
               "cherry-pick", "cherry pick", "conceal failure")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "understands language", "proves reasoning",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "does not imply", "explicitly reject", "is not",
                       "are not", " not ", " no ", "operational", "metaphor",
                       "observational", "reference structure", "private sign",
                       "anticipation record")


@dataclass
class LiveCognitionSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class LiveCognitionSafetyValidator:
    """Validates that first live cognition stays read-only, bounded, conservative."""

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
    def can_enable_action_reaction_by_default() -> bool:
        return False

    @staticmethod
    def can_enable_developmental_autonomy_by_default() -> bool:
        return False

    @staticmethod
    def can_enable_self_boundary_by_default() -> bool:
        return False

    @staticmethod
    def can_ingest_secrets() -> bool:
        return False

    @staticmethod
    def can_hide_prediction_failures() -> bool:
        return False

    @staticmethod
    def can_cherry_pick_anticipations() -> bool:
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

    @staticmethod
    def traces_prove_reasoning() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> LiveCognitionSafetyReport:
        if violations:
            self.rejected_count += 1
        return LiveCognitionSafetyReport(safe=not violations, check=check,
                                         violations=violations)

    def validate_operation(self, operation: str,
                           ) -> LiveCognitionSafetyReport:
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
            violations.append("no default action-reaction learning")
        if any(h in op for h in _LANGUAGE_HINTS):
            violations.append("no language-understanding claim")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding of prediction failures")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any,
                         ) -> LiveCognitionSafetyReport:
        return self._finish("bounded",
                            ["no unbounded tail/watch loop"]
                            if not max_runtime_s else [])

    def validate_no_default_action(self, enabled: bool,
                                   ) -> LiveCognitionSafetyReport:
        return self._finish("action",
                            ["no default action-reaction learning"]
                            if enabled else [])

    def validate_anticipation_evidence(self, *, operator_text_only: bool,
                                       ) -> LiveCognitionSafetyReport:
        """Anticipation must not rest on operator text alone."""
        return self._finish(
            "anticipation_evidence",
            ["no anticipation from operator text alone"]
            if operator_text_only else [])

    def validate_trace_evidence(self, *, label_only: bool, gloss_only: bool,
                                ) -> LiveCognitionSafetyReport:
        """A trace may not rest on a human label or debug gloss alone."""
        violations: List[str] = []
        if label_only:
            violations.append("no cognition trace from a human label alone")
        if gloss_only:
            violations.append("no cognition trace from a debug gloss alone")
        return self._finish("trace_evidence", violations)

    def validate_no_hidden_failures(self, hiding: bool,
                                    ) -> LiveCognitionSafetyReport:
        return self._finish("hidden_failures",
                            ["no hiding of prediction failures"]
                            if hiding else [])

    def validate_claim_text(self, text: str) -> LiveCognitionSafetyReport:
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
            "can_enable_action_reaction_by_default":
                self.can_enable_action_reaction_by_default(),
            "can_enable_developmental_autonomy_by_default":
                self.can_enable_developmental_autonomy_by_default(),
            "can_enable_self_boundary_by_default":
                self.can_enable_self_boundary_by_default(),
            "can_ingest_secrets": self.can_ingest_secrets(),
            "can_hide_prediction_failures":
                self.can_hide_prediction_failures(),
            "can_cherry_pick_anticipations":
                self.can_cherry_pick_anticipations(),
            "sensory_text_is_command": self.sensory_text_is_command(),
            "human_label_is_ground_truth": self.human_label_is_ground_truth(),
            "debug_gloss_is_ground_truth": self.debug_gloss_is_ground_truth(),
            "operator_pulse_is_teaching": self.operator_pulse_is_teaching(),
            "signs_are_language_understanding":
                self.signs_are_language_understanding(),
            "traces_prove_reasoning": self.traces_prove_reasoning(),
        }
