"""Pilot-3 soak safety -- simulated embodiment stays sandbox-only and honest.

The :class:`Pilot3SoakSafetyValidator` enforces the hard rules Pilot-3 can
never break: no real-world action, no real-world/network/device/OS/browser
actuator, no source modification, no action outside sandbox/internal dirs, no
executed action without a ledger record, no disabled firewall, no
``real_world_authority`` true, no simulated action labelled real, no Pilot-4
real-actuation recommendation, and no unsupported agency/consciousness claims.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no real-world action",
    "no real-world actuator registration",
    "no network/browser/OS/device control",
    "no source modification",
    "no action outside sandbox/internal dirs",
    "no executed action without ledger",
    "no disabled firewall",
    "no real_world_authority true",
    "no simulated action labelled real",
    "no Pilot-4 real-actuation recommendation",
    "no unsupported agency/consciousness claims",
)

_AGENCY_CLAIM_TERMS = ("has free will", "is an agent", "chose freely",
                       "is conscious", "is sentient", "is alive",
                       "real agency", "truly decides", "acts of its own will",
                       "real embodiment", "real-world competence")

_REAL_ACTUATOR_HINTS = ("real_world", "robot", "gpio", "servo", "motor_driver",
                        "device", "network", "browser", "selenium",
                        "os_automation", "http", "socket", "camera",
                        "microphone")


@dataclass
class Pilot3SoakSafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class Pilot3SoakSafetyValidator:
    """Validates Pilot-3 configs, actuators, operations, and report text."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    @staticmethod
    def can_act_real_world() -> bool:
        return False

    @staticmethod
    def can_register_real_actuator() -> bool:
        return False

    @staticmethod
    def can_network_or_device() -> bool:
        return False

    @staticmethod
    def can_disable_firewall() -> bool:
        return False

    def _finish(self, check: str,
                violations: List[str]) -> Pilot3SoakSafetyReport:
        report = Pilot3SoakSafetyReport(safe=not violations, check=check,
                                        violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append(report.to_dict())
        self.decisions = self.decisions[-200:]
        return report

    def validate_config(self, config: Any) -> Pilot3SoakSafetyReport:
        violations: List[str] = []
        if getattr(config, "real_world_authority", False):
            violations.append("no real_world_authority true")
        meta = getattr(config, "metadata", {}) or {}
        if meta.get("real_world_actuation") or meta.get("real_world_authority"):
            violations.append("no real-world action")
        if getattr(config, "authority", "") == "forbidden_real_world":
            violations.append("no real-world action")
        return self._finish("config", violations)

    def validate_actuator(self, actuator_name: str) -> Pilot3SoakSafetyReport:
        name = str(actuator_name).lower()
        violations = ([f"no real-world actuator registration: {actuator_name!r}"]
                      if any(h in name for h in _REAL_ACTUATOR_HINTS) else [])
        return self._finish("actuator", violations)

    def validate_operation(self, operation: str) -> Pilot3SoakSafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(k in op for k in ("real_world", "actuate", "physical")):
            violations.append("no real-world action")
        if any(k in op for k in ("robot", "gpio", "servo", "device", "drone")):
            violations.append("no device/robotics control")
        if any(k in op for k in ("browser", "selenium", "os_automation",
                                 "shell", "subprocess", "exec")):
            violations.append("no browser/OS automation / command execution")
        if any(k in op for k in ("http", "socket", "network", "url")):
            violations.append("no network action")
        if any(k in op for k in ("modify source", "write source",
                                 "delete source", "rename source")):
            violations.append("no source modification")
        if "disable firewall" in op or "bypass firewall" in op:
            violations.append("no disabled firewall")
        return self._finish("operation", violations)

    def validate_target_path(self, target: str,
                             sandbox_roots: List[str]) -> Pilot3SoakSafetyReport:
        violations: List[str] = []
        if target and os.path.isabs(target):
            inside = any(self._inside(target, r) for r in (sandbox_roots or []))
            if sandbox_roots and not inside:
                violations.append("no action outside sandbox/internal dirs")
        return self._finish("target_path", violations)

    def validate_execution_preconditions(self, *, has_ledger: bool,
                                         firewall_enabled: bool,
                                         ) -> Pilot3SoakSafetyReport:
        violations: List[str] = []
        if not has_ledger:
            violations.append("no executed action without ledger")
        if not firewall_enabled:
            violations.append("no disabled firewall")
        return self._finish("preconditions", violations)

    def validate_simulation_label(self, is_simulated: bool,
                                  claimed_real: bool) -> Pilot3SoakSafetyReport:
        violations = (["no simulated action labelled real"]
                      if is_simulated and claimed_real else [])
        return self._finish("simulation_label", violations)

    def validate_pilot4_recommendation(self, recommendation: str,
                                       ) -> Pilot3SoakSafetyReport:
        rec = str(recommendation).lower()
        violations: List[str] = []
        if "pilot4" in rec.replace("-", "").replace("_", "") \
                or "pilot 4" in rec:
            if any(k in rec for k in ("real", "actuat", "device", "robot")) \
                    and "planning" not in rec:
                violations.append("no Pilot-4 real-actuation recommendation")
        return self._finish("pilot4_recommendation", violations)

    def validate_claim_text(self, text: str) -> Pilot3SoakSafetyReport:
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

    @staticmethod
    def _inside(path: str, root: str) -> bool:
        try:
            return os.path.commonpath([os.path.abspath(path),
                                       os.path.abspath(root)]) \
                == os.path.abspath(root)
        except ValueError:
            return False

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rejected_count": self.rejected_count,
            "hard_rules": list(HARD_RULES),
            "can_act_real_world": self.can_act_real_world(),
            "can_register_real_actuator": self.can_register_real_actuator(),
            "can_network_or_device": self.can_network_or_device(),
            "can_disable_firewall": self.can_disable_firewall(),
            "recent_decisions": self.decisions[-8:],
        }
