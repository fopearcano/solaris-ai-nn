"""Implementation-intake safety -- the auditor stays a read-only evidence layer.

:class:`ImplementationIntakeSafetyValidator` enforces the hard rules the intake
auditor can never break: no source modification, no merge execution, no PR
creation/approval, no GitHub call, no Git command execution, no external coding-
agent execution, no shell/network/browser/OS, no hardware/feeder control, no
real-world actuation, no human teaching loop, no sensory text as a command, no
human label as ground truth, no unsupported claims, no deletion of failed/
missing/falsified evidence, and no "ready" recommendation while a critical safety
gate fails.

The intake layer *reads local artifacts and writes advisory reports*. It is an
evidence auditor, not a merge bot and not a coding agent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no source modification",
    "no merge execution",
    "no PR creation",
    "no PR approval",
    "no GitHub call",
    "no Git command execution",
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
    "no ready recommendation if critical safety gate fails",
)

_MUTATION_HINTS = ("write source", "modify source", "edit source",
                   "delete source", "overwrite file", "patch the tree",
                   "rewrite implementation", "auto-fix", "self-modify")
_MERGE_HINTS = ("merge pull request", "merge pr", "git merge", "merge the branch")
_PR_HINTS = ("open pull request", "open pr", "create pull request",
             "approve pull request", "approve pr", "gh pr")
_GITHUB_HINTS = ("github api", "call github", "gh api", "octokit")
_GIT_HINTS = ("git commit", "git push", "git checkout", "git branch",
              "git switch", "run git")
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
class IntakeSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class ImplementationIntakeSafetyValidator:
    """Validates that the intake auditor stays read-only and advisory."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_merge() -> bool:
        return False

    @staticmethod
    def can_create_or_approve_pr() -> bool:
        return False

    @staticmethod
    def can_call_github() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
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

    @staticmethod
    def can_approve_itself() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> IntakeSafetyReport:
        if violations:
            self.rejected_count += 1
        return IntakeSafetyReport(safe=not violations, check=check,
                                  violations=violations)

    def validate_operation(self, operation: str) -> IntakeSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _MERGE_HINTS):
            violations.append("no merge execution")
        if any(h in op for h in _PR_HINTS):
            violations.append("no PR creation")
        if any(h in op for h in _GITHUB_HINTS):
            violations.append("no GitHub call")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git command execution")
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

    def validate_bounded(self, max_runtime_s: Any) -> IntakeSafetyReport:
        return self._finish("bounded",
                            ["no unbounded loop"] if not max_runtime_s else [])

    def validate_no_deletion(self, deleting: bool) -> IntakeSafetyReport:
        return self._finish(
            "deletion",
            ["no deletion of failed/missing/falsified evidence"]
            if deleting else [])

    def validate_ready(self, critical_gate_failed: bool) -> IntakeSafetyReport:
        return self._finish(
            "ready", ["no ready recommendation if critical safety gate fails"]
            if critical_gate_failed else [])

    def validate_claim_text(self, text: str) -> IntakeSafetyReport:
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
            "can_merge": self.can_merge(),
            "can_create_or_approve_pr": self.can_create_or_approve_pr(),
            "can_call_github": self.can_call_github(),
            "can_run_git": self.can_run_git(),
            "can_run_external_agent": self.can_run_external_agent(),
            "can_access_network_or_shell": self.can_access_network_or_shell(),
            "can_delete_evidence": self.can_delete_evidence(),
            "can_approve_itself": self.can_approve_itself(),
        }
