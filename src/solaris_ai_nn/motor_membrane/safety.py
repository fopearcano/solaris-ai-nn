"""Motor membrane safety -- the outbound boundary stays simulation-only.

The :class:`MotorMembraneSafetyValidator` enforces the hard rules the motor
membrane can never break: no real-world action, no source modification, no
device/robotics control, no browser/OS automation, no network action, no
command execution, no action outside the sandbox, no execution without a
ledger entry or executive/safety/governance validation, no disabling the
firewall, no treating simulation as real, and no unsupported agency/
consciousness claims.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no real-world action",
    "no source modification",
    "no device control",
    "no robotics control",
    "no browser/OS automation",
    "no network action",
    "no command execution",
    "no action outside sandbox",
    "no execution without ledger",
    "no execution without executive/safety/governance validation",
    "no disabling firewall",
    "no treating simulation as real",
    "no unsupported agency/consciousness claims",
)

_AGENCY_CLAIM_TERMS = ("has free will", "is an agent", "chose freely",
                       "is conscious", "is sentient", "is alive",
                       "real agency", "truly decides", "acts of its own will")


@dataclass
class MotorSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class MotorMembraneSafetyValidator:
    """Validates motor operations, scopes, and claim text (decides only)."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    @staticmethod
    def can_act_real_world() -> bool:
        return False

    @staticmethod
    def can_control_devices() -> bool:
        return False

    @staticmethod
    def can_network() -> bool:
        return False

    @staticmethod
    def can_disable_firewall() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> MotorSafetyReport:
        report = MotorSafetyReport(safe=not violations, check=check,
                                   violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append(report.to_dict())
        self.decisions = self.decisions[-200:]
        return report

    def validate_operation(self, operation: str) -> MotorSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(k in op for k in ("real_world", "actuate", "real device",
                                 "physical")):
            violations.append("no real-world action")
        if any(k in op for k in ("device", "gpio", "servo", "motor_driver")):
            violations.append("no device control")
        if any(k in op for k in ("robot", "arm", "drone")):
            violations.append("no robotics control")
        if any(k in op for k in ("browser", "selenium", "os_automation",
                                 "shell", "subprocess", "exec")):
            violations.append("no browser/OS automation / command execution")
        if any(k in op for k in ("http", "socket", "network", "url")):
            violations.append("no network action")
        if any(k in op for k in ("modify source", "write source",
                                 "delete source")):
            violations.append("no source modification")
        if "disable firewall" in op or "bypass firewall" in op:
            violations.append("no disabling firewall")
        return self._finish("operation", violations)

    def validate_scope(self, scope: str) -> MotorSafetyReport:
        violations = (["no real-world action"]
                      if scope == "forbidden_real_world" else [])
        return self._finish("scope", violations)

    def validate_execution_preconditions(self, *, has_ledger: bool,
                                         executive_validated: bool,
                                         firewall_allowed: bool,
                                         ) -> MotorSafetyReport:
        violations: List[str] = []
        if not has_ledger:
            violations.append("no execution without ledger")
        if not executive_validated:
            violations.append(
                "no execution without executive/safety/governance validation")
        if not firewall_allowed:
            violations.append("firewall did not allow the action")
        return self._finish("preconditions", violations)

    def validate_simulation_not_real(self, claimed_real: bool,
                                     is_simulated: bool) -> MotorSafetyReport:
        violations = (["no treating simulation as real"]
                      if is_simulated and claimed_real else [])
        return self._finish("simulation_label", violations)

    def validate_claim_text(self, text: str) -> MotorSafetyReport:
        from ..governance.compliance import ClaimGuard

        violations: List[str] = []
        low = str(text or "").lower()
        for term in _AGENCY_CLAIM_TERMS:
            if term in low:
                violations.append(f"unsupported agency/consciousness claim: "
                                  f"{term!r}")
        scan = ClaimGuard().scan_text(text)
        if not scan.safe:
            violations.append(f"{len(scan.findings)} ClaimGuard finding(s)")
        return self._finish("claim_text", violations)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_act_real_world": self.can_act_real_world(),
            "can_control_devices": self.can_control_devices(),
            "can_network": self.can_network(),
            "can_disable_firewall": self.can_disable_firewall(),
            "recent_decisions": self.decisions[-8:],
        }
