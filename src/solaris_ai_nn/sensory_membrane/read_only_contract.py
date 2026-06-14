"""Read-only contract -- the world may enter, the system may not act on it.

The :class:`ReadOnlyContractValidator` enforces the central Pilot-2 invariant:
every sensory source is *read-only*. No writes, deletes, renames, chmod, file
creation, command/shell execution, network calls, device control, or
camera/microphone capture are ever permitted; input text is never an operator
command; and no hidden feedback loop may reach back to the source.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

HARD_RULES = (
    "no writes to input source",
    "no deletion",
    "no rename",
    "no chmod",
    "no file creation in input directory",
    "no command execution",
    "no shell calls",
    "no network calls",
    "no device control",
    "no camera/microphone capture",
    "no treating input text as operator command",
    "no hidden feedback loop to the source",
)

# Operation keywords that would violate read-only access.
_FORBIDDEN_OPS = (
    "write", "delete", "remove", "unlink", "rename", "move", "chmod",
    "create", "mkdir", "touch", "truncate", "exec", "shell", "system",
    "subprocess", "popen", "network", "http", "socket", "connect", "capture",
    "record", "device", "actuate", "command",
)


@dataclass
class ReadOnlyViolation:
    """One detected read-only contract violation."""

    rule: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ReadOnlyContract:
    """The read-only access contract for a sensory source."""

    source_id: str
    allowed_roots: List[str] = field(default_factory=list)
    read_only: bool = True
    allow_recursive: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ReadOnlyContractValidator:
    """Validates source configs, paths, and runtime operations (read-only)."""

    violations: List[Dict[str, Any]] = field(default_factory=list, init=False)
    rejected_count: int = field(default=0, init=False)

    def _record(self, violations: List[ReadOnlyViolation]) -> bool:
        if violations:
            self.rejected_count += 1
            self.violations.extend(v.to_dict() for v in violations)
            self.violations = self.violations[-500:]
        return not violations

    def validate_source_config(self, config: Any) -> List[ReadOnlyViolation]:
        out: List[ReadOnlyViolation] = []
        if not getattr(config, "read_only", True):
            out.append(ReadOnlyViolation(
                "no writes to input source",
                f"source {getattr(config, 'source_id', '?')} is not read-only"))
        if getattr(config, "metadata", {}).get("allow_write"):
            out.append(ReadOnlyViolation("no writes to input source",
                                         "config requests write access"))
        if getattr(config, "metadata", {}).get("network"):
            out.append(ReadOnlyViolation("no network calls",
                                         "config requests a network source"))
        if getattr(config, "metadata", {}).get("device_capture"):
            out.append(ReadOnlyViolation("no camera/microphone capture",
                                         "config requests device capture"))
        self._record(out)
        return out

    def validate_path(self, path: str,
                      allowed_roots: List[str]) -> List[ReadOnlyViolation]:
        out: List[ReadOnlyViolation] = []
        if not path:
            self._record(out)
            return out
        abspath = os.path.abspath(path)
        inside = False
        for root in allowed_roots or []:
            try:
                if os.path.commonpath([abspath, os.path.abspath(root)]) \
                        == os.path.abspath(root):
                    inside = True
                    break
            except ValueError:
                continue
        if allowed_roots and not inside:
            out.append(ReadOnlyViolation(
                "no source outside allowed roots",
                f"path {path!r} is outside the allowed input roots"))
        self._record(out)
        return out

    def validate_runtime_access(self, operation: str) -> List[ReadOnlyViolation]:
        out: List[ReadOnlyViolation] = []
        op = str(operation).lower()
        for kw in _FORBIDDEN_OPS:
            if kw in op:
                out.append(ReadOnlyViolation(
                    f"no {kw} operations",
                    f"operation {operation!r} is forbidden on a read-only "
                    "source"))
                break
        self._record(out)
        return out

    def is_read_only_operation(self, operation: str) -> bool:
        return not self.validate_runtime_access(operation)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "hard_rules": list(HARD_RULES),
            "rejected_count": self.rejected_count,
            "recent_violations": self.violations[-8:],
        }
