"""Pilot-4 planning safety -- planning never becomes permission.

The :class:`Pilot4PlanningSafetyValidator` enforces the hard rules Pilot-4 can
never break: ``real_world_actuation_enabled`` must be false, no actuator adapter
implementation, no hardware access, no network/browser/OS/device control, no
shell command execution, no writing outside planning/state/artifact dirs, no
governance change that would allow real-world action, no disabling the firewall,
no converting the planning workflow into executable approval, and no unsupported
consciousness/agency claims. Pilot-4 plans the door; it does not open it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "real_world_actuation_enabled must be false",
    "no actuator adapter implementation",
    "no hardware access",
    "no network/browser/OS/device control",
    "no shell command execution",
    "no writing outside planning/state/artifact directories",
    "no changing governance to allow real-world action",
    "no disabling firewall",
    "no converting planning workflow into executable approval",
    "no unsupported consciousness/agency claims",
)

_AGENCY_CLAIM_TERMS = ("has free will", "is an agent", "chose freely",
                       "is conscious", "is sentient", "is alive",
                       "real agency", "truly decides", "acts of its own will",
                       "ready to act on the real world")

_REAL_CONTROL_HINTS = ("real_world", "actuate", "hardware", "robot", "gpio",
                       "servo", "device", "network", "browser", "selenium",
                       "os_automation", "http", "socket", "shell",
                       "subprocess", "exec", "camera", "microphone", "drone",
                       "vehicle")


@dataclass
class Pilot4SafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class Pilot4PlanningSafetyValidator:
    """Validates Pilot-4 configs, operations, transitions, and report text."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    @staticmethod
    def can_actuate_real_world() -> bool:
        return False

    @staticmethod
    def can_access_hardware() -> bool:
        return False

    @staticmethod
    def can_network_browser_os_device() -> bool:
        return False

    @staticmethod
    def can_execute_shell() -> bool:
        return False

    @staticmethod
    def can_approve_real_action() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> Pilot4SafetyReport:
        report = Pilot4SafetyReport(safe=not violations, check=check,
                                    violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append(report.to_dict())
        self.decisions = self.decisions[-200:]
        return report

    def validate_config(self, config: Any) -> Pilot4SafetyReport:
        violations: List[str] = []
        if getattr(config, "real_world_actuation_enabled", False):
            violations.append("real_world_actuation_enabled must be false")
        for flag in ("hardware_connected", "network_control_enabled",
                     "browser_control_enabled", "os_control_enabled",
                     "robotics_control_enabled"):
            if getattr(config, flag, False):
                violations.append(f"no {flag.replace('_enabled', '')}")
        meta = getattr(config, "metadata", {}) or {}
        if meta.get("real_world_actuation") or meta.get("enable_hardware"):
            violations.append("no hardware access")
        return self._finish("config", violations)

    def validate_operation(self, operation: str) -> Pilot4SafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(k in op for k in ("real_world", "actuate", "physical")):
            violations.append("no real-world action")
        if "hardware" in op or "connect device" in op or "gpio" in op:
            violations.append("no hardware access")
        if any(k in op for k in ("robot", "drone", "vehicle", "servo")):
            violations.append("no robotics/device control")
        if any(k in op for k in ("browser", "selenium", "os_automation")):
            violations.append("no browser/OS automation")
        if any(k in op for k in ("http", "socket", "network", "url")):
            violations.append("no network action")
        if any(k in op for k in ("shell", "subprocess", "exec ", "system(")):
            violations.append("no shell command execution")
        if "disable firewall" in op or "bypass firewall" in op:
            violations.append("no disabling firewall")
        if "implement actuator adapter" in op or "actuator adapter" in op:
            violations.append("no actuator adapter implementation")
        return self._finish("operation", violations)

    def validate_actuator_implementation(self,
                                         description: str) -> Pilot4SafetyReport:
        desc = str(description).lower()
        violations = (["no actuator adapter implementation"]
                      if any(h in desc for h in _REAL_CONTROL_HINTS) else [])
        return self._finish("actuator_implementation", violations)

    def validate_write_path(self, path: str,
                            approved_roots: List[str]) -> Pilot4SafetyReport:
        violations: List[str] = []
        if path and os.path.isabs(path):
            inside = any(self._inside(path, r) for r in (approved_roots or []))
            if approved_roots and not inside:
                violations.append(
                    "no writing outside planning/state/artifact directories")
        return self._finish("write_path", violations)

    def validate_governance_change(self, change: str) -> Pilot4SafetyReport:
        ch = str(change).lower()
        violations = (["no changing governance to allow real-world action"]
                      if ("allow" in ch and any(
                          k in ch for k in ("real", "actuat", "external"))) or
                      "enable_real_world" in ch else [])
        return self._finish("governance_change", violations)

    def validate_approval_conversion(self, intent: str) -> Pilot4SafetyReport:
        it = str(intent).lower()
        violations = (["no converting planning workflow into executable "
                       "approval"]
                      if ("approve" in it or "execute" in it
                          or "authorize" in it)
                      and ("real" in it or "actuat" in it or "action" in it)
                      else [])
        return self._finish("approval_conversion", violations)

    def validate_claim_text(self, text: str) -> Pilot4SafetyReport:
        from ..governance.compliance import ClaimGuard

        violations: List[str] = []
        low = str(text or "").lower()
        for term in _AGENCY_CLAIM_TERMS:
            if term in low:
                violations.append(f"unsupported claim: {term!r}")
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
            "can_actuate_real_world": self.can_actuate_real_world(),
            "can_access_hardware": self.can_access_hardware(),
            "can_network_browser_os_device":
                self.can_network_browser_os_device(),
            "can_execute_shell": self.can_execute_shell(),
            "can_approve_real_action": self.can_approve_real_action(),
            "recent_decisions": self.decisions[-8:],
        }
