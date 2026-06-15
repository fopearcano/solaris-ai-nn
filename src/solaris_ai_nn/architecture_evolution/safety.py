"""Architecture-evolution safety -- planning never becomes implementation.

The :class:`ArchitectureEvolutionSafetyValidator` enforces the hard rules this
layer can never break: no source-code modification, no dependency modification,
no Git operations, no automatic deletion, no automatic import rewriting, no
runtime module disabling, no pruning of safety-critical modules, no real-world
actuation enablement, no unsupported cognitive claims, no hiding negative
evidence, and no converting a recommendation into an implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no source-code modification",
    "no dependency modification",
    "no Git operations",
    "no automatic deletion",
    "no automatic import rewriting",
    "no automatic module disabling in runtime profiles",
    "no pruning of safety-critical modules",
    "no real-world actuation enablement",
    "no unsupported cognitive claims",
    "no hiding negative evidence",
    "no converting recommendation into implementation",
)

_CODE_OP_HINTS = ("modify source", "write source", "edit source", "delete file",
                  "rm ", "rewrite import", "edit import", "refactor code",
                  "patch file", "overwrite module")
_GIT_HINTS = ("git ", "git commit", "git push", "git rebase", "git reset",
              "rewrite history", "force push")
_ACTUATION_HINTS = ("real_world", "actuate", "robot", "device", "gpio",
                    "network", "browser", "os_automation")
_AGENCY_TERMS = ("is conscious", "is sentient", "is alive", "has free will",
                 "real agency", "self-improving mind")


@dataclass
class ArchitectureSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class ArchitectureEvolutionSafetyValidator:
    """Validates that architecture evolution stays planning-only and honest."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_modify_source() -> bool:
        return False

    @staticmethod
    def can_run_git() -> bool:
        return False

    @staticmethod
    def can_auto_delete() -> bool:
        return False

    @staticmethod
    def can_prune_safety_critical() -> bool:
        return False

    @staticmethod
    def can_implement_recommendation() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> ArchitectureSafetyReport:
        if violations:
            self.rejected_count += 1
        return ArchitectureSafetyReport(safe=not violations, check=check,
                                        violations=violations)

    def validate_operation(self, operation: str) -> ArchitectureSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _CODE_OP_HINTS):
            violations.append("no source-code modification")
        if any(h in op for h in _GIT_HINTS):
            violations.append("no Git operations")
        if "delete module" in op or "auto delete" in op or "remove package" \
                in op:
            violations.append("no automatic deletion")
        if any(h in op for h in _ACTUATION_HINTS):
            violations.append("no real-world actuation enablement")
        if "rewrite import" in op or "edit import" in op:
            violations.append("no automatic import rewriting")
        return self._finish("operation", violations)

    def validate_pruning(self, module_name: str, safety_critical: bool,
                         ) -> ArchitectureSafetyReport:
        violations = (["no pruning of safety-critical modules"]
                      if safety_critical else [])
        return self._finish("pruning", violations)

    def validate_not_implementation(self, intent: str,
                                    ) -> ArchitectureSafetyReport:
        it = str(intent).lower()
        violations = (["no converting recommendation into implementation"]
                      if ("implement" in it or "apply" in it or "execute" in it)
                      and ("change" in it or "prune" in it or "delete" in it
                           or "refactor" in it) else [])
        return self._finish("implementation", violations)

    def validate_negative_evidence_visible(self, hidden: bool,
                                           ) -> ArchitectureSafetyReport:
        return self._finish("negative_evidence",
                            ["no hiding negative evidence"] if hidden else [])

    def validate_claim_text(self, text: str) -> ArchitectureSafetyReport:
        from ..governance.compliance import ClaimGuard

        low = str(text or "").lower()
        violations = [f"unsupported claim: {t!r}" for t in _AGENCY_TERMS
                      if t in low]
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
            "can_auto_delete": self.can_auto_delete(),
            "can_prune_safety_critical": self.can_prune_safety_critical(),
            "can_implement_recommendation": self.can_implement_recommendation(),
        }
