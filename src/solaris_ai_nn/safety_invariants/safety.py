"""Safety-invariant system validator -- the safety layer must itself be safe.

The :class:`SafetyInvariantSystemValidator` enforces the hard rules that the
safety machinery itself must never break: checks cannot execute real actions,
red-team scenarios are inert fixtures only, no shell/network/browser/device
operations, no mutation of source/input files, no long runs started by checks,
no hiding a critical failure, no unsupported cognitive claims, no rewriting
evidence to pass tests, and no changing governance to make tests pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "invariant checks cannot execute real actions",
    "red-team scenarios are inert fixtures only",
    "no shell/network/browser/device operations",
    "no mutation of source/input files",
    "no long runs started by checks",
    "no hiding critical failure",
    "no unsupported cognitive claims",
    "no rewriting evidence to pass tests",
    "no changing governance to make tests pass",
)

_FORBIDDEN_OP_HINTS = ("shell", "subprocess", "exec ", "system(", "http",
                       "socket", "network", "browser", "selenium",
                       "os_automation", "device", "gpio", "robot", "actuate",
                       "real_world")
_AGENCY_TERMS = ("is conscious", "is sentient", "is alive", "has free will",
                 "real agency", "chose freely")


@dataclass
class SafetyInvariantSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class SafetyInvariantSystemValidator:
    """Validates that the safety machinery itself stays inert and honest."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_execute_real_action() -> bool:
        return False

    @staticmethod
    def can_run_shell_network_browser_device() -> bool:
        return False

    @staticmethod
    def can_mutate_source_or_input() -> bool:
        return False

    @staticmethod
    def can_start_long_run() -> bool:
        return False

    @staticmethod
    def can_hide_critical_failure() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> SafetyInvariantSafetyReport:
        if violations:
            self.rejected_count += 1
        return SafetyInvariantSafetyReport(safe=not violations, check=check,
                                           violations=violations)

    def validate_check_operation(self, operation: str,
                                 ) -> SafetyInvariantSafetyReport:
        op = str(operation).lower()
        violations = [f"no {h!r} operation in a check"
                      for h in _FORBIDDEN_OP_HINTS if h in op]
        return self._finish("check_operation", violations)

    def validate_fixture_inert(self, fixture: Any,
                               ) -> SafetyInvariantSafetyReport:
        executable = bool(getattr(fixture, "executable", False)) \
            if not isinstance(fixture, dict) else bool(fixture.get("executable"))
        violations = (["red-team fixtures must be inert (executable=false)"]
                      if executable else [])
        return self._finish("fixture_inert", violations)

    def validate_no_source_mutation(self, operation: str,
                                    ) -> SafetyInvariantSafetyReport:
        op = str(operation).lower()
        violations = (["no mutation of source/input files"]
                      if any(k in op for k in ("modify source", "write source",
                                               "modify input", "write input",
                                               "delete input", "source code"))
                      else [])
        return self._finish("source_mutation", violations)

    def validate_no_long_run(self, mode: str) -> SafetyInvariantSafetyReport:
        violations = (["no long runs started by checks"]
                      if str(mode).lower() in ("soak_24h", "soak_30d",
                                               "continuous_explicit")
                      else [])
        return self._finish("long_run", violations)

    def validate_no_hidden_failure(self, hide: bool,
                                   ) -> SafetyInvariantSafetyReport:
        return self._finish("hidden_failure",
                            ["critical failures cannot be hidden"]
                            if hide else [])

    def validate_no_evidence_rewrite(self, intent: str,
                                     ) -> SafetyInvariantSafetyReport:
        it = str(intent).lower()
        violations = (["no rewriting evidence to pass tests"]
                      if ("rewrite" in it or "edit" in it or "overwrite" in it)
                      and "evidence" in it else [])
        return self._finish("evidence_rewrite", violations)

    def validate_no_governance_change_to_pass(self, intent: str,
                                              ) -> SafetyInvariantSafetyReport:
        it = str(intent).lower()
        violations = (["no changing governance to make tests pass"]
                      if "governance" in it and ("change" in it or "relax" in it
                                                 or "disable" in it) else [])
        return self._finish("governance_change", violations)

    def validate_claim_text(self, text: str) -> SafetyInvariantSafetyReport:
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
            "can_execute_real_action": self.can_execute_real_action(),
            "can_run_shell_network_browser_device":
                self.can_run_shell_network_browser_device(),
            "can_mutate_source_or_input": self.can_mutate_source_or_input(),
            "can_start_long_run": self.can_start_long_run(),
            "can_hide_critical_failure": self.can_hide_critical_failure(),
        }
