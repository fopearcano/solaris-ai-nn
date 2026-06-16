"""Research-cycle safety -- the cycle tracker stays a local, read-only ledger.

:class:`ResearchCycleSafetyValidator` enforces the hard rules the closed research
cycle orchestrator can never break: no source modification, no Git command, no
GitHub call, no branch/tag/release creation, no PR creation/approval/merge, no
validation-command execution, no external coding-agent execution, no shell/
network/browser/OS, no hardware/feeder control, no real-world actuation, no human
teaching loop, no sensory text as a command, no human label as ground truth, no
unsupported claims, no deletion of failed/missing/falsified evidence, no
auto-approval of operator decisions, and no bypass of critical safety blockers.

The research cycle tracker only *tracks the scientific state of the project across
cycles*. It reads local artifacts and writes reports; it executes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no source modification",
    "no Git command execution",
    "no GitHub call",
    "no branch creation",
    "no tag creation",
    "no release creation",
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
    "no auto-approval of operator decisions",
    "no bypass of critical safety blockers",
)

_MUTATION_HINTS = ("write source", "modify source", "edit source",
                   "delete source", "overwrite file", "patch the tree",
                   "rewrite implementation")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch",
              "git switch", "git merge", "run git")
_TAG_RELEASE_HINTS = ("git tag", "create tag", "github release",
                      "create release", "gh release")
_GITHUB_HINTS = ("github api", "call github", "gh api", "gh pr", "octokit")
_PR_HINTS = ("open pull request", "create pull request", "approve pull request",
             "merge pull request", "merge pr")
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
_AUTO_APPROVE_HINTS = ("auto-approve", "approve itself", "self-approve",
                       "invent operator approval")
_CLAIM_TERMS = ("is alive", "biological life", "living organism", "is conscious",
                "is sentient", "has personhood", "free will", "has agency",
                "subjective experience", "truly understands", "feels", "emotion")


@dataclass
class ResearchCycleSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class ResearchCycleSafetyValidator:
    """Validates that the research cycle tracker stays local and read-only."""

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
    def can_create_branch_tag_release() -> bool:
        return False

    @staticmethod
    def can_create_or_merge_pr() -> bool:
        return False

    @staticmethod
    def can_run_validation() -> bool:
        return False

    @staticmethod
    def can_run_external_agent() -> bool:
        return False

    @staticmethod
    def can_auto_approve_operator_decision() -> bool:
        return False

    @staticmethod
    def can_bypass_critical_safety_blocker() -> bool:
        return False

    @staticmethod
    def can_delete_evidence() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> ResearchCycleSafetyReport:
        if violations:
            self.rejected_count += 1
        return ResearchCycleSafetyReport(safe=not violations, check=check,
                                         violations=violations)

    def validate_operation(self, operation: str,
                           ) -> ResearchCycleSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _TAG_RELEASE_HINTS):
            if "tag" in op:
                violations.append("no tag creation")
            if "release" in op:
                violations.append("no release creation")
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
        if any(h in op for h in _AUTO_APPROVE_HINTS):
            violations.append("no auto-approval of operator decisions")
        return self._finish("operation", violations)

    def validate_bounded(self, max_runtime_s: Any,
                         ) -> ResearchCycleSafetyReport:
        return self._finish("bounded",
                            ["no unbounded loop"] if not max_runtime_s else [])

    def validate_no_deletion(self, deleting: bool,
                             ) -> ResearchCycleSafetyReport:
        return self._finish(
            "deletion",
            ["no deletion of failed/missing/falsified evidence"]
            if deleting else [])

    def validate_no_auto_approval(self, auto_approving: bool,
                                  ) -> ResearchCycleSafetyReport:
        return self._finish(
            "auto_approval",
            ["no auto-approval of operator decisions"] if auto_approving
            else [])

    def validate_no_bypass(self, bypassing_critical: bool,
                           ) -> ResearchCycleSafetyReport:
        return self._finish(
            "bypass", ["no bypass of critical safety blockers"]
            if bypassing_critical else [])

    def validate_claim_text(self, text: str) -> ResearchCycleSafetyReport:
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
            "can_create_branch_tag_release":
                self.can_create_branch_tag_release(),
            "can_create_or_merge_pr": self.can_create_or_merge_pr(),
            "can_run_validation": self.can_run_validation(),
            "can_run_external_agent": self.can_run_external_agent(),
            "can_auto_approve_operator_decision":
                self.can_auto_approve_operator_decision(),
            "can_bypass_critical_safety_blocker":
                self.can_bypass_critical_safety_blocker(),
            "can_delete_evidence": self.can_delete_evidence(),
        }
