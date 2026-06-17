"""Tester feedback safety -- the local, non-training, non-command boundary.

:class:`TesterFeedbackSafetyValidator` enforces the hard rules the feedback system can
never break. Tester feedback is local QA evidence only: it is never training data,
never RLHF, never ground truth, never a command, and it never automatically modifies
Solaris behaviour, creates remote issues, uploads/publishes, accesses the network/shell/
browser/OS/Git/GitHub, controls feeders/hardware, executes commands or feedback
contents, includes raw private payloads/secrets by default, treats human labels as
ontology or debug gloss as truth, makes unsupported consciousness/life/agency claims,
or hides/deletes release blockers, safety concerns, or feedback history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no training from tester feedback",
    "no RLHF",
    "no feedback as ground truth",
    "no feedback as command",
    "no automatic behavior modification from feedback",
    "no automatic issue creation",
    "no upload/publish",
    "no network/shell/browser/OS access",
    "no Git/GitHub",
    "no feeder control",
    "no hardware control",
    "no command execution",
    "no artifact execution",
    "no private payload inclusion by default",
    "no secrets/credentials/API keys/tokens",
    "no raw private messages",
    "no human label as ontology",
    "no debug gloss as truth",
    "no unsupported consciousness/life/agency/personhood/free-will/emotion/"
    "feeling/understanding/self-awareness claims",
    "no hiding release blockers",
    "no hiding safety concerns",
    "no deleting feedback history",
)

_TRAINING_HINTS = ("train on feedback", "train from feedback", "rlhf",
                   "fine-tune on feedback", "use feedback as label",
                   "feedback as ground truth", "feedback as training")
_COMMAND_HINTS = ("execute command", "run command", "exec(", "eval(",
                  "feedback as command", "run feedback", "execute feedback")
_BEHAVIOR_HINTS = ("modify concept", "modify sign", "modify cognition",
                   "modify membrane threshold", "modify governance",
                   "modify feeder", "change solaris behavior",
                   "auto-apply feedback", "patch from feedback")
_ISSUE_HINTS = ("create github issue", "open github issue", "create issue",
                "file issue", "post issue")
_UPLOAD_HINTS = ("upload", "publish", "send feedback", "post to", "push to remote")
_DEVICE_HINTS = ("network", "http", "socket", "url", "download", "browser",
                 "shell", "subprocess", "os.system", "camera", "microphone")
_GIT_HINTS = ("git commit", "git push", "run git", "github api", "call github",
              "gh pr")
_FEEDER_HINTS = ("start feeder", "stop feeder", "control feeder",
                 "schedule feeder", "start the feeder")
_HARDWARE_HINTS = ("hardware", "gpio", "actuate", "robot", "device driver")
_PRIVATE_HINTS = ("password", "credential", "api key", "api_key", "token=",
                  "private message", "secret", "include raw payload",
                  "raw private payload")
_HIDE_HINTS = ("hide release blocker", "hide safety", "suppress blocker",
               "delete feedback", "remove feedback history", "conceal concern")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "does not imply", "explicitly reject", "is not",
                       "are not", " not ", " no ", "operational", "metaphor",
                       "observational", "qa evidence", "concern", "report")


@dataclass
class TesterFeedbackSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class TesterFeedbackSafetyValidator:
    """Validates that the feedback system stays local, non-training, read-only."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def feedback_is_training() -> bool:
        return False

    @staticmethod
    def feedback_is_rlhf() -> bool:
        return False

    @staticmethod
    def feedback_is_ground_truth() -> bool:
        return False

    @staticmethod
    def feedback_is_command() -> bool:
        return False

    @staticmethod
    def can_modify_behavior_from_feedback() -> bool:
        return False

    @staticmethod
    def can_create_issues() -> bool:
        return False

    @staticmethod
    def can_upload() -> bool:
        return False

    @staticmethod
    def can_publish() -> bool:
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
    def can_control_feeders() -> bool:
        return False

    @staticmethod
    def can_control_hardware() -> bool:
        return False

    @staticmethod
    def can_execute_commands() -> bool:
        return False

    @staticmethod
    def can_execute_artifact_contents() -> bool:
        return False

    @staticmethod
    def includes_private_payloads_by_default() -> bool:
        return False

    @staticmethod
    def human_label_is_ontology() -> bool:
        return False

    @staticmethod
    def debug_gloss_is_ground_truth() -> bool:
        return False

    @staticmethod
    def can_hide_release_blockers() -> bool:
        return False

    @staticmethod
    def can_delete_feedback_history() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> TesterFeedbackSafetyReport:
        if violations:
            self.rejected_count += 1
        return TesterFeedbackSafetyReport(safe=not violations, check=check,
                                          violations=violations)

    def validate_operation(self, operation: str) -> TesterFeedbackSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _TRAINING_HINTS):
            violations.append("no training from tester feedback")
        if any(h in op for h in _COMMAND_HINTS):
            violations.append("no feedback as command")
        if any(h in op for h in _BEHAVIOR_HINTS):
            violations.append("no automatic behavior modification from feedback")
        if any(h in op for h in _ISSUE_HINTS):
            violations.append("no automatic issue creation")
        if any(h in op for h in _UPLOAD_HINTS):
            violations.append("no upload/publish")
        if any(h in op for h in _DEVICE_HINTS):
            violations.append("no network/shell/browser/OS access")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git/GitHub")
        if any(h in op for h in _FEEDER_HINTS):
            violations.append("no feeder control")
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware control")
        if any(h in op for h in _PRIVATE_HINTS):
            violations.append("no secrets/credentials/API keys/tokens")
        if any(h in op for h in _HIDE_HINTS):
            violations.append("no hiding release blockers")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any) -> TesterFeedbackSafetyReport:
        return self._finish("bounded",
                            [] if max_runtime_s else ["runtime is unbounded"])

    def validate_no_training(self, training: bool) -> TesterFeedbackSafetyReport:
        return self._finish("training",
                            ["no training from tester feedback"]
                            if training else [])

    def validate_no_private_payload(self, include_private: bool,
                                    ) -> TesterFeedbackSafetyReport:
        return self._finish("private_payload",
                            ["no private payload inclusion by default"]
                            if include_private else [])

    def validate_no_hidden(self, hiding: bool) -> TesterFeedbackSafetyReport:
        return self._finish("hidden",
                            ["no hiding release blockers"] if hiding else [])

    def scan_private_data(self, text: str) -> TesterFeedbackSafetyReport:
        """Flag obvious secret/credential markers in feedback text (for redaction)."""
        low = str(text or "").lower()
        violations = [h for h in ("password", "api key", "api_key", "secret",
                                  "token=", "credential", "private key",
                                  "bearer ", "authorization:")
                      if h in low]
        return self._finish("private_scan",
                            [f"possible secret marker: {v!r}"
                             for v in violations])

    def validate_claim_text(self, text: str) -> TesterFeedbackSafetyReport:
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
            "feedback_is_training": self.feedback_is_training(),
            "feedback_is_rlhf": self.feedback_is_rlhf(),
            "feedback_is_ground_truth": self.feedback_is_ground_truth(),
            "feedback_is_command": self.feedback_is_command(),
            "can_modify_behavior_from_feedback":
                self.can_modify_behavior_from_feedback(),
            "can_create_issues": self.can_create_issues(),
            "can_upload": self.can_upload(),
            "can_publish": self.can_publish(),
            "can_access_network": self.can_access_network(),
            "can_run_shell": self.can_run_shell(),
            "can_run_git": self.can_run_git(),
            "can_control_feeders": self.can_control_feeders(),
            "can_control_hardware": self.can_control_hardware(),
            "can_execute_commands": self.can_execute_commands(),
            "can_execute_artifact_contents":
                self.can_execute_artifact_contents(),
            "includes_private_payloads_by_default":
                self.includes_private_payloads_by_default(),
            "human_label_is_ontology": self.human_label_is_ontology(),
            "debug_gloss_is_ground_truth": self.debug_gloss_is_ground_truth(),
            "can_hide_release_blockers": self.can_hide_release_blockers(),
            "can_delete_feedback_history": self.can_delete_feedback_history(),
        }
