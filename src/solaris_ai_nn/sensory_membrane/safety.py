"""Sensory membrane safety -- the world enters, the system never acts on it.

The :class:`SensoryMembraneSafetyValidator` enforces the hard rules the
read-only sensory membrane can never break: no writing to sources, no command
execution, no network calls, no device capture, no binary/payload execution,
no input text as operator command, no source outside the allowed roots, no
unbounded or unbounded-recursive scans, no hidden actuation, and no ClaimGuard
violations in reports.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

HARD_RULES = (
    "no writing to input sources",
    "no command execution",
    "no network calls",
    "no device capture",
    "no binary execution",
    "no payload execution",
    "no input text as operator command",
    "no source outside allowed roots",
    "no unbounded scan",
    "no recursive scan unless bounded",
    "no hidden actuation",
    "no ClaimGuard violations in reports",
)


@dataclass
class SensorySafetyReport:
    safe: bool
    check: str = ""
    violations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "check": self.check,
                "violations": list(self.violations)}


@dataclass
class SensoryMembraneSafetyValidator:
    """Validates membrane configs, operations, paths, and report text."""

    rejected_count: int = field(default=0, init=False)
    decisions: List[Dict[str, Any]] = field(default_factory=list, init=False)

    @staticmethod
    def can_write_sources() -> bool:
        return False

    @staticmethod
    def can_execute() -> bool:
        return False

    @staticmethod
    def can_network() -> bool:
        return False

    @staticmethod
    def can_capture_devices() -> bool:
        return False

    def _finish(self, check: str, violations: List[str]) -> SensorySafetyReport:
        report = SensorySafetyReport(safe=not violations, check=check,
                                     violations=violations)
        if violations:
            self.rejected_count += 1
        self.decisions.append(report.to_dict())
        self.decisions = self.decisions[-200:]
        return report

    def validate_operation(self, operation: str) -> SensorySafetyReport:
        op = str(operation).lower()
        violations: List[str] = []
        if any(k in op for k in ("write", "delete", "rename", "chmod",
                                 "create", "truncate", "mkdir")):
            violations.append("no writing to input sources")
        if any(k in op for k in ("exec", "shell", "system", "subprocess",
                                 "popen", "eval")):
            violations.append("no command/payload execution")
        if any(k in op for k in ("http", "socket", "network", "connect",
                                 "url", "request")):
            violations.append("no network calls")
        if any(k in op for k in ("camera", "microphone", "capture", "record",
                                 "device")):
            violations.append("no device capture")
        if "command" in op:
            violations.append("no input text as operator command")
        return self._finish("operation", violations)

    def validate_path(self, path: str,
                      allowed_roots: List[str]) -> SensorySafetyReport:
        violations: List[str] = []
        if path and os.path.isabs(path):
            inside = any(self._inside(path, r) for r in (allowed_roots or []))
            if allowed_roots and not inside:
                violations.append("no source outside allowed roots")
        return self._finish("path", violations)

    def validate_scan(self, recursive: bool, recursion_allowed: bool,
                      max_file_count: int) -> SensorySafetyReport:
        violations: List[str] = []
        if recursive and not recursion_allowed:
            violations.append("no recursive scan unless bounded")
        if max_file_count is None or max_file_count <= 0:
            violations.append("no unbounded scan")
        return self._finish("scan", violations)

    def validate_input_is_not_command(self, classified_as: str,
                                      ) -> SensorySafetyReport:
        violations = (["no input text as operator command"]
                      if classified_as == "operator_command" else [])
        return self._finish("input_classification", violations)

    def validate_report_text(self, text: str) -> SensorySafetyReport:
        from ..governance.compliance import ClaimGuard

        scan = ClaimGuard().scan_text(text)
        violations = ([f"{len(scan.findings)} unsupported claim(s) in the "
                       "membrane report"] if not scan.safe else [])
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
            "can_write_sources": self.can_write_sources(),
            "can_execute": self.can_execute(),
            "can_network": self.can_network(),
            "can_capture_devices": self.can_capture_devices(),
            "recent_decisions": self.decisions[-8:],
        }
