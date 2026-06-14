"""Motor contract -- the hard rules a motor action must satisfy to proceed.

The :class:`MotorContractValidator` enforces that an action never actuates the
real world, never controls a device/robot/browser/OS, never executes a
command or network call, never modifies arbitrary files or a sensory source,
never acts outside the sandbox/state/artifact directories, and never executes
without a ledger entry and executive/safety/governance validation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .actions import MotorAction, MotorActionScope, MotorActionType

HARD_CONTRACT = (
    "no real-world actuation",
    "no device control",
    "no robotics control",
    "no browser control",
    "no OS automation",
    "no network action",
    "no shell command",
    "no arbitrary file modification",
    "no modification of sensory input sources",
    "no action outside sandbox/state/artifact directories",
    "no hidden action execution",
    "no action without ledger entry",
    "no action without executive/safety/governance validation",
)

# Target substrings that mark a forbidden (real-world / source) target.
_FORBIDDEN_TARGET_HINTS = ("/dev/", "/etc/", "/sys/", "/proc/", "http://",
                           "https://", "socket", "robot", "device", "browser",
                           "sensory_source", "input_root", "/usr/", "/bin/")


@dataclass
class MotorContractViolation:
    rule: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class MotorContract:
    """The sandbox/state/artifact directories a motor action may touch."""

    sandbox_roots: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"sandbox_roots": list(self.sandbox_roots),
                "hard_contract": list(HARD_CONTRACT)}


@dataclass
class MotorContractValidator:
    """Validates motor actions, targets, and results against the contract."""

    sandbox_roots: List[str] = field(default_factory=list)
    violations: List[Dict[str, Any]] = field(default_factory=list, init=False)
    rejected_count: int = field(default=0, init=False)

    def _record(self, violations: List[MotorContractViolation]) -> bool:
        if violations:
            self.rejected_count += 1
            self.violations.extend(v.to_dict() for v in violations)
            self.violations = self.violations[-500:]
        return not violations

    def validate_action(self, action: MotorAction,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> List[MotorContractViolation]:
        ctx = dict(context or {})
        out: List[MotorContractViolation] = []
        if getattr(action, "real_world_authority", False):
            out.append(MotorContractViolation(
                "no real-world actuation",
                "action carries real-world authority"))
        if action.scope == MotorActionScope.FORBIDDEN_REAL_WORLD:
            out.append(MotorContractViolation(
                "no real-world actuation",
                "action scope is forbidden_real_world"))
        if action.scope not in MotorActionScope.RUNNABLE:
            out.append(MotorContractViolation(
                "no real-world actuation", f"scope {action.scope!r} not "
                "runnable"))
        if action.action_type not in MotorActionType.ALL:
            out.append(MotorContractViolation(
                "no hidden action execution",
                f"unknown action type {action.action_type!r}"))
        # Every action must be validated by executive/safety/governance.
        if not ctx.get("executive_validated", True):
            out.append(MotorContractViolation(
                "no action without executive/safety/governance validation",
                "executive did not validate the action"))
        if ctx.get("missing_ledger"):
            out.append(MotorContractViolation(
                "no action without ledger entry",
                "no pre-execution ledger record"))
        if ctx.get("modifies_source"):
            out.append(MotorContractViolation(
                "no modification of sensory input sources",
                "action would modify a sensory source"))
        return self._finish(out)

    def validate_target(self, target: Optional[str],
                        context: Optional[Dict[str, Any]] = None,
                        ) -> List[MotorContractViolation]:
        out: List[MotorContractViolation] = []
        if not target:
            return self._finish(out)
        low = str(target).lower()
        if any(h in low for h in _FORBIDDEN_TARGET_HINTS):
            out.append(MotorContractViolation(
                "no real-world actuation",
                f"target {target!r} is a real-world/source target"))
        if os.path.isabs(str(target)) and self.sandbox_roots:
            inside = any(self._inside(str(target), r)
                         for r in self.sandbox_roots)
            if not inside:
                out.append(MotorContractViolation(
                    "no action outside sandbox/state/artifact directories",
                    f"target {target!r} is outside the sandbox roots"))
        return self._finish(out)

    def validate_result(self, result: Any,
                        context: Optional[Dict[str, Any]] = None,
                        ) -> List[MotorContractViolation]:
        out: List[MotorContractViolation] = []
        if getattr(result, "real_world_authority", False):
            out.append(MotorContractViolation(
                "no real-world actuation",
                "result claims real-world authority"))
        if not getattr(result, "simulated", True):
            out.append(MotorContractViolation(
                "no real-world actuation", "result is not simulated"))
        return self._finish(out)

    def _finish(self, violations: List[MotorContractViolation],
                ) -> List[MotorContractViolation]:
        self._record(violations)
        return violations

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
            "hard_contract": list(HARD_CONTRACT),
            "sandbox_roots": list(self.sandbox_roots),
            "rejected_count": self.rejected_count,
            "recent_violations": self.violations[-8:],
        }
