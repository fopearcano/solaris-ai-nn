"""Command registry check -- verify the tester CLI commands are registered.

:class:`CommandRegistryCheck` reads the CLI handler registry (read-only) and verifies the
required tester commands are present (a missing required command blocks packaging
readiness) and reports missing optional commands as warnings. It never runs a command
(it may, at most, reference ``--help``); it has no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

_REQUIRED = (
    "doctor", "tester-demo", "tester-golden", "tester-bundle", "tester-repro",
    "tester-regression", "tester-fixtures", "tester-live-init",
    "tester-live-doctor", "tester-live-samples", "tester-live-run",
    "tester-live-bundle", "tester-live-checklist", "tester-console",
    "tester-console-status", "tester-feedback-init", "tester-feedback-ingest",
    "tester-feedback-report", "tester-feedback-ledger", "tester-feedback-bundle",
    "tester-feedback-blockers", "membrane-doctor", "membrane-run",
    "membrane-integrate", "membrane-audit",
)

_OPTIONAL = (
    "live-birth", "live-observe", "live-ontogenesis", "live-semiogenesis",
    "live-cognition", "build-report", "alpha-demo",
)


@dataclass
class RegisteredCommand:
    """One command's registration status."""

    name: str
    required: bool
    registered: bool

    @property
    def blocking(self) -> bool:
        return self.required and not self.registered

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "required": self.required,
                "registered": self.registered, "blocking": self.blocking}


@dataclass
class CommandCheckResult:
    """The aggregate command registry check result."""

    commands: List[RegisteredCommand] = field(default_factory=list)

    @property
    def missing_required(self) -> List[str]:
        return [c.name for c in self.commands if c.blocking]

    @property
    def missing_optional(self) -> List[str]:
        return [c.name for c in self.commands
                if not c.required and not c.registered]

    @property
    def passed(self) -> bool:
        return not self.missing_required

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "command_count": len(self.commands),
            "registered_count": sum(1 for c in self.commands if c.registered),
            "missing_required_count": len(self.missing_required),
            "missing_optional_count": len(self.missing_optional),
            "missing_required": list(self.missing_required),
            "missing_optional": list(self.missing_optional),
            "commands": [c.to_dict() for c in self.commands],
            "runs_commands": False,
            "note": "read-only command registry check; it does not run any "
                    "command (it never executes side effects)",
        }


@dataclass
class CommandRegistryCheck:
    """Read-only check of the tester CLI command registry."""

    def check(self) -> CommandCheckResult:
        registered = self._registered_commands()
        result = CommandCheckResult()
        for name in _REQUIRED:
            result.commands.append(RegisteredCommand(
                name=name, required=True, registered=name in registered))
        for name in _OPTIONAL:
            result.commands.append(RegisteredCommand(
                name=name, required=False, registered=name in registered))
        return result

    @staticmethod
    def _registered_commands() -> set:
        try:
            from ..cli import _HANDLERS
        except Exception:
            return set()
        return set(_HANDLERS.keys())
