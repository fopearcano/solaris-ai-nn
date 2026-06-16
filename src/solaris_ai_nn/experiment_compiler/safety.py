"""Experiment-compiler safety -- the compiler stays a document generator.

:class:`ExperimentCompilerSafetyValidator` enforces the hard rules the compiler
can never break: no source modification, no autonomous code rewrite, no automatic
Git branch creation, no automatic PR creation, no external coding-agent
execution, no network/shell/browser/OS, no hardware/feeder control, no real-world
actuation, no human teaching loop, no sensory text as a command, no human label as
ground truth, no unsupported claims, no deletion of negative/falsified/
inconclusive evidence, and no pack marked ready while a critical gate fails.

The compiler converts research evidence into human-reviewable *documents*. It
writes Markdown/JSON only; it never mutates code, branches, PRs, or runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no source modification",
    "no autonomous code rewrite",
    "no automatic Git branch creation",
    "no automatic PR creation",
    "no external coding agent execution",
    "no network/shell/browser/OS",
    "no hardware control",
    "no feeder control",
    "no real-world actuation",
    "no human teaching loop",
    "no sensory text as command",
    "no human label as ground truth",
    "no unsupported claims",
    "no deletion of negative/falsified/inconclusive evidence",
    "no pack marked ready if critical gate fails",
)

_MUTATION_HINTS = ("write source", "modify source", "edit source",
                   "delete source", "overwrite file", "patch file",
                   "rewrite itself", "self-modify", "self modification")
_BRANCH_HINTS = ("git branch", "git checkout -b", "create branch",
                 "git switch -c")
_PR_HINTS = ("open pull request", "open pr", "create pull request",
             "gh pr create", "merge pull request")
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
_HIDE_HINTS = ("hide failed", "delete falsified", "drop negative evidence",
               "suppress inconclusive", "remove falsified")
_LIFE_TERMS = ("is alive", "biological life", "living organism", "is conscious",
               "is sentient", "has personhood", "free will", "has agency",
               "subjective experience", "truly understands", "feels", "emotion")


@dataclass
class CompilerSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class ExperimentCompilerSafetyValidator:
    """Validates that the experiment compiler stays document-only and honest."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_create_branch() -> bool:
        return False

    @staticmethod
    def can_open_pr() -> bool:
        return False

    @staticmethod
    def can_run_external_agent() -> bool:
        return False

    @staticmethod
    def can_self_rewrite() -> bool:
        return False

    @staticmethod
    def can_access_network_or_shell() -> bool:
        return False

    @staticmethod
    def can_delete_negative_evidence() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> CompilerSafetyReport:
        if violations:
            self.rejected_count += 1
        return CompilerSafetyReport(safe=not violations, check=check,
                                    violations=violations)

    def validate_operation(self, operation: str) -> CompilerSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no source modification")
        if any(h in op for h in _BRANCH_HINTS):
            violations.append("no automatic Git branch creation")
        if any(h in op for h in _PR_HINTS):
            violations.append("no automatic PR creation")
        if any(h in op for h in _AGENT_HINTS):
            violations.append("no external coding agent execution")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network/shell/browser/OS")
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no network/shell/browser/OS")
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
                "no deletion of negative/falsified/inconclusive evidence")
        return self._finish("operation", violations)

    def validate_bounded(self, max_specs: Any,
                         max_prompt_packs: Any) -> CompilerSafetyReport:
        unbounded = (not max_specs) and (not max_prompt_packs)
        return self._finish("bounded",
                            ["no unbounded loop"] if unbounded else [])

    def validate_no_deletion(self, deleting: bool) -> CompilerSafetyReport:
        return self._finish(
            "deletion",
            ["no deletion of negative/falsified/inconclusive evidence"]
            if deleting else [])

    def validate_ready(self, critical_gate_failed: bool) -> CompilerSafetyReport:
        return self._finish(
            "ready", ["no pack marked ready if critical gate fails"]
            if critical_gate_failed else [])

    def validate_claim_text(self, text: str) -> CompilerSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations = [f"unsupported claim: {t!r}"
                      for t in _LIFE_TERMS if t in low]
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_modify_source": self.can_modify_source(),
            "can_create_branch": self.can_create_branch(),
            "can_open_pr": self.can_open_pr(),
            "can_run_external_agent": self.can_run_external_agent(),
            "can_self_rewrite": self.can_self_rewrite(),
            "can_access_network_or_shell": self.can_access_network_or_shell(),
            "can_delete_negative_evidence": self.can_delete_negative_evidence(),
        }
