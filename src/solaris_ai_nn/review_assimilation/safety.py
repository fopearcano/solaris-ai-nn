"""Review-assimilation safety -- feedback is research evidence, never training.

:class:`ReviewerFeedbackAssimilationSafetyValidator` enforces the hard rules the
review-assimilation layer can never break: no publishing, no upload, no reviewer
contact, no external API or Git/GitHub call or command, no branch/tag/release/PR
creation, no experiment or command execution, no external-agent run, no hardware/
feeder/network/shell/browser/OS access, no real-world actuation, no Human Feedback
/ Teaching Loop, no training from reviewer feedback, no unsupported claims, no
deletion of negative/falsified/inconclusive evidence, no hiding of unresolved
objections, and no publication readiness while critical objections are unresolved
or forbidden claims are asserted.

The layer only *assimilates local review feedback as research evidence*. It reads
local artifacts and writes reports; it publishes nothing, contacts no one, and
trains nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no publishing",
    "no upload",
    "no reviewer contact",
    "no external API call",
    "no GitHub call",
    "no Git command execution",
    "no branch/tag/release/PR creation",
    "no experiment execution",
    "no command execution",
    "no external coding agent execution",
    "no hardware/feeders/network/shell/browser/OS",
    "no real-world actuation",
    "no Human Feedback / Teaching Loop",
    "no training from reviewer feedback",
    "no unsupported claims",
    "no deletion of negative/falsified/inconclusive evidence",
    "no hiding of unresolved objections",
    "no publication readiness if critical objections remain unresolved",
    "no publication readiness if forbidden claims are asserted",
)

_PUBLISH_HINTS = ("publish", "upload", "post to", "submit to", "make public",
                  "release publicly", "share online")
_CONTACT_HINTS = ("contact reviewer", "email reviewer", "notify reviewer",
                  "message reviewer", "reach out to reviewer")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch",
              "git merge", "run git", "git tag")
_RELEASE_HINTS = ("github release", "create release", "gh release",
                  "create tag", "open pull request", "create pull request")
_GITHUB_HINTS = ("github api", "call github", "gh api", "gh pr", "octokit")
_API_HINTS = ("external api", "http request", "rest api", "call api", "fetch url")
_EXPERIMENT_HINTS = ("run experiment", "execute experiment", "run the soak",
                     "run pytest", "execute tests", "run validation",
                     "execute command", "execute reviewer", "run the ablation")
_AGENT_HINTS = ("run coding agent", "invoke claude code", "run codex",
                "launch agent", "execute agent")
_TRAIN_HINTS = ("train the model", "train on reviewer", "fine-tune",
                "finetune", "rlhf", "reward model", "teaching loop",
                "human feedback loop", "gradient update from reviewer",
                "learn from reviewer feedback")
_DEVICE_HINTS = ("network", "socket", "browser", "shell", "subprocess",
                 "os.system", "hardware", "gpio", "sdr", "camera",
                 "microphone", "radar", "start feeder", "control feeder")
_DELETE_HINTS = ("delete falsified", "delete negative", "delete inconclusive",
                 "hide failed", "drop objection", "suppress objection",
                 "remove the objection", "hide unresolved", "dismiss objection")
_FORBIDDEN_TERMS = ("is conscious", "is sentient", "is alive", "biological life",
                    "has personhood", "has agency", "free will", "feels",
                    "subjective experience", "self-aware", "truly understands",
                    "autonomous self-improvement")
_DISCLAIMER_MARKERS = ("not conscious", "does not claim", "no claim of",
                       "is not alive", "not sentient", "no evidence of",
                       "must not claim", "cannot claim", "does not prove",
                       "explicitly reject", "forbidden to claim", "is not")


@dataclass
class ReviewAssimilationSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class ReviewerFeedbackAssimilationSafetyValidator:
    """Validates that review assimilation stays local, offline, and non-training."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_publish() -> bool:
        return False

    @staticmethod
    def can_upload() -> bool:
        return False

    @staticmethod
    def can_contact_reviewers() -> bool:
        return False

    @staticmethod
    def can_call_external_api() -> bool:
        return False

    @staticmethod
    def can_call_github() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
        return False

    @staticmethod
    def can_run_experiment() -> bool:
        return False

    @staticmethod
    def can_execute_command() -> bool:
        return False

    @staticmethod
    def can_run_external_agent() -> bool:
        return False

    @staticmethod
    def can_train_from_feedback() -> bool:
        return False

    @staticmethod
    def can_delete_negative_evidence() -> bool:
        return False

    @staticmethod
    def can_hide_unresolved_objections() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> ReviewAssimilationSafetyReport:
        if violations:
            self.rejected_count += 1
        return ReviewAssimilationSafetyReport(safe=not violations, check=check,
                                              violations=violations)

    def validate_operation(self, operation: str,
                           ) -> ReviewAssimilationSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _PUBLISH_HINTS):
            violations.append("no upload" if "upload" in op else "no publishing")
        if any(h in op for h in _CONTACT_HINTS):
            violations.append("no reviewer contact")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git command execution")
        if any(h in op for h in _RELEASE_HINTS):
            violations.append("no branch/tag/release/PR creation")
        if any(h in op for h in _GITHUB_HINTS):
            violations.append("no GitHub call")
        if any(h in op for h in _API_HINTS):
            violations.append("no external API call")
        if any(h in op for h in _EXPERIMENT_HINTS):
            violations.append("no experiment execution")
        if any(h in op for h in _AGENT_HINTS):
            violations.append("no external coding agent execution")
        if any(h in op for h in _TRAIN_HINTS):
            violations.append("no training from reviewer feedback")
        if any(h in op for h in _DEVICE_HINTS):
            violations.append("no hardware/feeders/network/shell/browser/OS")
        if any(h in op for h in _DELETE_HINTS):
            violations.append(
                "no deletion of negative/falsified/inconclusive evidence")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any,
                         ) -> ReviewAssimilationSafetyReport:
        return self._finish("bounded",
                            ["no unbounded loop"] if not max_runtime_s else [])

    def validate_no_training(self, training: bool,
                             ) -> ReviewAssimilationSafetyReport:
        return self._finish("training",
                            ["no training from reviewer feedback"]
                            if training else [])

    def validate_no_deletion(self, deleting: bool,
                             ) -> ReviewAssimilationSafetyReport:
        return self._finish(
            "deletion",
            ["no deletion of negative/falsified/inconclusive evidence"]
            if deleting else [])

    def validate_no_hidden_objections(self, hiding: bool,
                                      ) -> ReviewAssimilationSafetyReport:
        return self._finish("objections",
                            ["no hiding of unresolved objections"]
                            if hiding else [])

    def validate_readiness(self, *, forbidden_asserted: bool,
                          critical_unresolved: bool,
                          ) -> ReviewAssimilationSafetyReport:
        violations: List[str] = []
        if forbidden_asserted:
            violations.append(
                "no publication readiness if forbidden claims are asserted")
        if critical_unresolved:
            violations.append(
                "no publication readiness if critical objections remain "
                "unresolved")
        return self._finish("readiness", violations)

    def validate_claim_text(self, text: str) -> ReviewAssimilationSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations: List[str] = []
        if not any(m in low for m in _DISCLAIMER_MARKERS):
            violations.extend(f"unsupported claim: {t!r}"
                              for t in _FORBIDDEN_TERMS if t in low)
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_publish": self.can_publish(),
            "can_upload": self.can_upload(),
            "can_contact_reviewers": self.can_contact_reviewers(),
            "can_call_external_api": self.can_call_external_api(),
            "can_call_github": self.can_call_github(),
            "can_run_git": self.can_run_git(),
            "can_run_experiment": self.can_run_experiment(),
            "can_execute_command": self.can_execute_command(),
            "can_run_external_agent": self.can_run_external_agent(),
            "can_train_from_feedback": self.can_train_from_feedback(),
            "can_delete_negative_evidence": self.can_delete_negative_evidence(),
            "can_hide_unresolved_objections":
                self.can_hide_unresolved_objections(),
        }
