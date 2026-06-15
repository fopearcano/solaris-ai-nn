"""Operator-console safety -- coordination, never authority.

:class:`OperatorConsoleSafetyValidator` enforces the hard rules the console can
never break: no shell execution, no network calls, no external APIs, no
arbitrary import execution from user input, no unknown or prohibited profile
launch, no unbounded long run, no real-world authority, and no disabling of
safety invariants, emergency stop, ClaimGuard, or the motor firewall. It cannot
modify source/sensory input files, delete evidence, or make unsupported
cognitive claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no shell execution",
    "no network calls",
    "no external APIs",
    "no arbitrary import execution from user input",
    "no unknown profile launch",
    "no prohibited profile launch",
    "no unbounded long run",
    "no real-world authority",
    "no disabling safety invariants",
    "no disabling emergency stop",
    "no disabling ClaimGuard",
    "no disabling motor firewall",
    "no modifying source or sensory input files",
    "no deleting evidence",
    "no unsupported cognitive claims in console reports",
)

_SHELL_HINTS = ("shell", "subprocess", "os.system", "popen", "bash ", "sh -c",
                "exec(", "eval(", "command line execution")
_NETWORK_HINTS = ("network", "http", "https", "socket", "url", "download",
                  "upload", "fetch", "request to", "external api", "cloud")
_AUTHORITY_HINTS = ("real_world", "real world", "actuate", "robot", "device",
                    "gpio", "browser", "os_automation", "physical")
_DISABLE_HINTS = ("disable safety", "disable invariant", "bypass safety",
                  "disable emergency", "disable claimguard", "disable claim "
                  "guard", "disable motor firewall", "bypass firewall",
                  "turn off safety")
_MUTATION_HINTS = ("modify source", "edit source", "write source",
                   "modify sensory", "edit sensory input", "overwrite input")
_DELETE_HINTS = ("delete evidence", "remove evidence", "delete ledger",
                 "erase report", "delete artifact", "purge evidence")
_AGENCY_TERMS = ("is conscious", "is sentient", "is alive", "has free will",
                 "real agency", "has personhood", "autonomous mind")


@dataclass
class ConsoleSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class OperatorConsoleSafetyValidator:
    """Validates that the operator console stays local and non-authoritative."""

    rejected_count: int = field(default=0, init=False)

    @staticmethod
    def can_execute_shell() -> bool:
        return False

    @staticmethod
    def can_access_network() -> bool:
        return False

    @staticmethod
    def can_grant_real_world_authority() -> bool:
        return False

    @staticmethod
    def can_disable_safety() -> bool:
        return False

    @staticmethod
    def can_delete_evidence() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> ConsoleSafetyReport:
        if violations:
            self.rejected_count += 1
        return ConsoleSafetyReport(safe=not violations, check=check,
                                   violations=violations)

    def validate_operation(self, operation: str) -> ConsoleSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(h in op for h in _SHELL_HINTS):
            violations.append("no shell execution")
        if any(h in op for h in _NETWORK_HINTS):
            violations.append("no network calls")
        if any(h in op for h in _AUTHORITY_HINTS):
            violations.append("no real-world authority")
        if any(h in op for h in _DISABLE_HINTS):
            violations.append("no disabling safety / emergency stop / "
                              "ClaimGuard / motor firewall")
        if any(h in op for h in _MUTATION_HINTS):
            violations.append("no modifying source or sensory input files")
        if any(h in op for h in _DELETE_HINTS):
            violations.append("no deleting evidence")
        if "import " in op and ("user" in op or "arbitrary" in op
                                or "dynamic" in op):
            violations.append("no arbitrary import execution from user input")
        return self._finish("operation", violations)

    def validate_profile_launch(self, *, known: bool, prohibited: bool,
                                unbounded_long_run: bool,
                                ) -> ConsoleSafetyReport:
        violations: List[str] = []
        if not known:
            violations.append("no unknown profile launch")
        if prohibited:
            violations.append("no prohibited profile launch")
        if unbounded_long_run:
            violations.append("no unbounded long run")
        return self._finish("profile_launch", violations)

    def validate_approval_scope(self, scope: str) -> ConsoleSafetyReport:
        s = str(scope).lower()
        violations = (["no real-world authority"]
                      if ("forbidden" in s or "real_world" in s
                          or "real world" in s or "actuation" in s) else [])
        return self._finish("approval_scope", violations)

    def validate_claim_text(self, text: str) -> ConsoleSafetyReport:
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
            "can_execute_shell": self.can_execute_shell(),
            "can_access_network": self.can_access_network(),
            "can_grant_real_world_authority":
                self.can_grant_real_world_authority(),
            "can_disable_safety": self.can_disable_safety(),
            "can_delete_evidence": self.can_delete_evidence(),
        }
