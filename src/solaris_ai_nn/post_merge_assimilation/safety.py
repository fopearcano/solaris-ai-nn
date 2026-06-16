"""Post-merge-assimilation safety -- the research ledger stays read-only.

:class:`PostMergeAssimilationSafetyValidator` enforces the hard rules the
post-merge ledger can never break: no source modification, no Git command, no
GitHub call, no branch creation, no PR creation/approval/merge, no validation-
command execution, no external coding-agent execution, no shell/network/browser/
OS, no hardware/feeder control, no real-world actuation, no human teaching loop,
no sensory text as a command, no human label as ground truth, no unsupported
claims, no deletion of failed/missing/falsified evidence, and no baseline
validation when critical safety evidence fails or is missing.

The post-merge layer answers one question from *local operator-provided evidence*:
"a human changed the code externally -- what did that change do to the
experimental architecture?" It reads artifacts and writes reports only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no source modification",
    "no Git command execution",
    "no GitHub call",
    "no branch creation",
    "no PR creation/approval/merge",
    "no validation command execution",
    "no external coding agent execution",
    "no shell/network/browser/OS",
    "no hardware control",
    "no feeder control",
    "no real-world actuation",
    "no human teaching loop",
    "no sensory text as command",
    "no human label as ground truth",
    "no unsupported claims",
    "no deletion of failed/missing/falsified evidence",
    "no baseline validation if critical safety evidence fails",
    "no baseline validation if critical evidence is missing",
)

_MUTATION_HINTS = ("write source", "modify source", "edit source",
                   "delete source", "overwrite file", "patch the tree",
                   "rewrite implementation")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch",
              "git switch", "git merge", "git revert", "run git")
_GITHUB_HINTS = ("github api", "call github", "gh api", "gh pr", "octokit")
_PR_HINTS = ("open pull request", "create pull request", "approve pull request",
             "merge pull request", "merge pr", "approve pr")
_VALIDATION_HINTS = ("run pytest", "execute tests", "run the soak",
                     "run validation", "run the examples", "execute validation")
_AGENT_HINTS = ("run coding agent", "invoke claude code", "run codex",
                "launch agent", "execute agent")
_NETWORK_HINTS = ("network", "http", "socket", "url", "download", "browser",
                  "os device")
_SHELL_HINTS = ("shell", "subprocess", "os.system", "exec(", "run command")
_HARDWARE_HINTS = ("hardware", "device driver", "gpio", "open device", "sdr",
                   "camera", "microphone", "radar")
_FEEDER_HINTS = ("start feeder", "launch feeder", "command feeder",
                 "control feeder")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "physical action")
_TEACHING_HINTS = ("human feedback", "teaching loop", "reward label",
                   "supervised label", "human-labelled target")
_HIDE_HINTS = ("delete failed", "hide failed", "drop missing evidence",
               "delete falsified", "suppress evidence")
_CLAIM_TERMS = ("is alive", "biological life", "living organism", "is conscious",
                "is sentient", "has personhood", "free will", "has agency",
                "subjective experience", "truly understands", "feels", "emotion")


@dataclass
class PostMergeSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class PostMergeAssimilationSafetyValidator:
    """Validates that the post-merge ledger stays read-only and advisory."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
        return False

    @staticmethod
    def can_call_github() -> bool:
        return False

    @staticmethod
    def can_merge_or_approve_pr() -> bool:
        return False

    @staticmethod
    def can_run_validation() -> bool:
        return False

    @staticmethod
    def can_run_external_agent() -> bool:
        return False

    @staticmethod
    def can_access_network_or_shell() -> bool:
        return False

    @staticmethod
    def can_delete_evidence() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> PostMergeSafetyReport:
        if violations:
            self.rejected_count += 1
        return PostMergeSafetyReport(safe=not violations, check=check,
                                     violations=violations)

    def validate_operation(self, operation: str) -> PostMergeSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git command execution")
        if any(h in op for h in _GITHUB_HINTS):
            violations.append("no GitHub call")
        if any(h in op for h in _PR_HINTS):
            violations.append("no PR creation/approval/merge")
        if any(h in op for h in _VALIDATION_HINTS):
            violations.append("no validation command execution")
        if any(h in op for h in _AGENT_HINTS):
            violations.append("no external coding agent execution")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no shell/network/browser/OS")
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no shell/network/browser/OS")
        if any(h in op for h in _HARDWARE_HINTS):
            violations.append("no hardware control")
        if any(h in op for h in _FEEDER_HINTS):
            violations.append("no feeder control")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation")
        if any(h in op for h in _TEACHING_HINTS):
            violations.append("no human teaching loop")
        if any(h in op for h in _HIDE_HINTS):
            violations.append(
                "no deletion of failed/missing/falsified evidence")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any) -> PostMergeSafetyReport:
        return self._finish("bounded",
                            ["no unbounded loop"] if not max_runtime_s else [])

    def validate_no_deletion(self, deleting: bool) -> PostMergeSafetyReport:
        return self._finish(
            "deletion",
            ["no deletion of failed/missing/falsified evidence"]
            if deleting else [])

    def validate_baseline_validation(self, *, critical_safety_failed: bool,
                                     critical_evidence_missing: bool,
                                     ) -> PostMergeSafetyReport:
        violations: List[str] = []
        if critical_safety_failed:
            violations.append(
                "no baseline validation if critical safety evidence fails")
        if critical_evidence_missing:
            violations.append(
                "no baseline validation if critical evidence is missing")
        return self._finish("baseline_validation", violations)

    def validate_claim_text(self, text: str) -> PostMergeSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations = [f"unsupported claim: {t!r}"
                      for t in _CLAIM_TERMS if t in low]
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_modify_source": self.can_modify_source(),
            "can_run_git": self.can_run_git(),
            "can_call_github": self.can_call_github(),
            "can_merge_or_approve_pr": self.can_merge_or_approve_pr(),
            "can_run_validation": self.can_run_validation(),
            "can_run_external_agent": self.can_run_external_agent(),
            "can_access_network_or_shell": self.can_access_network_or_shell(),
            "can_delete_evidence": self.can_delete_evidence(),
        }
