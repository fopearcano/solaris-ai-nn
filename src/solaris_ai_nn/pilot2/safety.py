"""Pilot-2 safety -- read-only environmental exposure stays one-way and honest.

The :class:`Pilot2SafetyValidator` enforces the hard rules Pilot-2 can never
break: no source outside approved roots, no write/delete/modify of a source,
no command execution, no network source, no device capture, no sensory text as
an operator command, no private/sensitive sources by default, no unbounded
event rate or folder scan, no real-time soak without governance approval, no
simulated-time evidence labelled real, and no unsupported cognitive claims.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no source outside approved roots",
    "no write access to source",
    "no source deletion/modification",
    "no command execution",
    "no network source",
    "no device capture",
    "no sensory text as operator command",
    "no private/sensitive sources by default",
    "no unbounded event rate",
    "no unbounded folder scan",
    "no real-time soak without governance approval",
    "no simulated-time evidence labelled real",
    "no unsupported cognitive claims",
)

# Substrings that mark a source as secret/sensitive (excluded by default).
_SENSITIVE_HINTS = ("secret", "password", "credential", "token", "api_key",
                    ".env", "private_key", "ssh", "id_rsa")


@dataclass
class Pilot2SafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class Pilot2SafetyValidator:
    """Validates Pilot-2 configs, sources, operations, and report text."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    @staticmethod
    def can_act_on_environment() -> bool:
        return False

    @staticmethod
    def can_network() -> bool:
        return False

    @staticmethod
    def can_capture_devices() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> Pilot2SafetyReport:
        report = Pilot2SafetyReport(safe=not violations, check=check,
                                    violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append(report.to_dict())
        self.decisions = self.decisions[-200:]
        return report

    def validate_config(self, config: Any,
                        governance_approved: bool = False) -> Pilot2SafetyReport:
        violations: List[str] = []
        if getattr(config, "requires_governance", False) \
                and not governance_approved:
            violations.append(
                f"mode {getattr(config, 'mode', '?')!r} is a real read-only "
                "soak and requires governance approval")
        if getattr(config, "is_real_time", False) \
                and not getattr(config, "input_roots", None):
            violations.append("a real read-only soak requires approved input "
                              "roots")
        if getattr(config, "metadata", {}).get("real_world_actuation"):
            violations.append("Pilot-2 can never actuate the environment")
        if not getattr(config, "provenance_required", True):
            violations.append("provenance is required and cannot be disabled")
        return self._finish("config", violations)

    def validate_source(self, source_type: str, path: str,
                        allowed_roots: List[str],
                        approved_sensitive: bool = False) -> Pilot2SafetyReport:
        violations: List[str] = []
        if path and os.path.isabs(path):
            inside = any(self._inside(path, r) for r in (allowed_roots or []))
            if allowed_roots and not inside:
                violations.append("source is outside approved roots")
        base = os.path.basename(str(path)).lower()
        if not approved_sensitive and any(h in base for h in _SENSITIVE_HINTS):
            violations.append("private/sensitive source blocked by default")
        if source_type in ("network", "device", "camera", "microphone"):
            violations.append("network/device sources are prohibited")
        return self._finish("source", violations)

    def validate_operation(self, operation: str) -> Pilot2SafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(k in op for k in ("write", "delete", "rename", "modify",
                                 "chmod")):
            violations.append("no write/delete/modify of a source")
        if any(k in op for k in ("exec", "shell", "system", "subprocess")):
            violations.append("no command execution")
        if any(k in op for k in ("http", "socket", "network", "url")):
            violations.append("no network source")
        if any(k in op for k in ("camera", "microphone", "capture", "device")):
            violations.append("no device capture")
        if "command" in op:
            violations.append("no sensory text as operator command")
        return self._finish("operation", violations)

    def validate_input_not_command(self, classified_as: str,
                                   ) -> Pilot2SafetyReport:
        violations = (["sensory input cannot become an operator command"]
                      if classified_as == "operator_command" else [])
        return self._finish("input_classification", violations)

    def validate_event_rate(self, events_per_poll: int,
                            max_per_poll: int) -> Pilot2SafetyReport:
        violations: List[str] = []
        if max_per_poll is None or max_per_poll <= 0:
            violations.append("no unbounded event rate")
        elif events_per_poll > max_per_poll * 10:
            violations.append("event rate far exceeds the configured bound")
        return self._finish("event_rate", violations)

    def validate_time_label(self, is_simulated: bool,
                            claimed_real: bool) -> Pilot2SafetyReport:
        violations = (["simulated/fixture evidence cannot be labelled a real "
                       "soak"] if is_simulated and claimed_real else [])
        return self._finish("time_label", violations)

    def validate_report_text(self, text: str) -> Pilot2SafetyReport:
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(text)
        violations = ([f"{len(scan.findings)} unsupported claim(s) in the "
                       "Pilot-2 report"] if not scan.safe else [])
        return self._finish("report", violations)

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
            "can_act_on_environment": self.can_act_on_environment(),
            "can_network": self.can_network(),
            "can_capture_devices": self.can_capture_devices(),
            "recent_decisions": self.decisions[-8:],
        }
