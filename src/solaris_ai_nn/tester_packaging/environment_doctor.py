"""Tester environment doctor -- read-only environment readiness checks.

:class:`TesterEnvironmentDoctor` checks the Python executable/version, package + CLI
import, the command registry, write permission to the tester/live state dirs, the
presence of example fixtures and tester modules (fixture spine, membrane, integration,
console, feedback), and the live templates/docs. It is read-only: it never auto-fixes,
runs long demos, starts feeders, accesses the network, runs shell, opens a browser, or
installs packages.
"""

from __future__ import annotations

import importlib
import os
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Any, Dict, List

_MIN_PYTHON = (3, 11)


class EnvironmentHealth:
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    BLOCKED = "blocked"
    MISSING = "missing"
    UNKNOWN = "unknown"

    ALL = (PASS, PASS_WITH_WARNINGS, BLOCKED, MISSING, UNKNOWN)


@dataclass
class EnvironmentFinding:
    """One environment doctor finding."""

    check: str
    health: str = EnvironmentHealth.UNKNOWN
    detail: str = ""
    required: bool = True

    @property
    def blocking(self) -> bool:
        return self.required and self.health in (EnvironmentHealth.BLOCKED,
                                                 EnvironmentHealth.MISSING)

    def to_dict(self) -> Dict[str, Any]:
        return {"check": self.check, "health": self.health,
                "detail": self.detail, "required": self.required,
                "blocking": self.blocking}


@dataclass
class EnvironmentDoctorResult:
    """The aggregate environment doctor result."""

    findings: List[EnvironmentFinding] = field(default_factory=list)

    @property
    def blockers(self) -> List[EnvironmentFinding]:
        return [f for f in self.findings if f.blocking]

    @property
    def warnings(self) -> List[EnvironmentFinding]:
        return [f for f in self.findings
                if f.health == EnvironmentHealth.PASS_WITH_WARNINGS
                or (not f.required and f.health in (EnvironmentHealth.MISSING,
                                                    EnvironmentHealth.BLOCKED))]

    @property
    def overall_health(self) -> str:
        if self.blockers:
            return EnvironmentHealth.BLOCKED
        if self.warnings:
            return EnvironmentHealth.PASS_WITH_WARNINGS
        return EnvironmentHealth.PASS

    @property
    def passed(self) -> bool:
        return not self.blockers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_health": self.overall_health,
            "passed": self.passed,
            "finding_count": len(self.findings),
            "blocker_count": len(self.blockers),
            "warning_count": len(self.warnings),
            "findings": [f.to_dict() for f in self.findings],
            "auto_fixes": False, "runs_demos": False, "installs": False,
            "accesses_network": False,
            "note": "read-only environment doctor; it never auto-fixes, runs "
                    "long demos, starts feeders, accesses the network, runs "
                    "shell, opens a browser, or installs packages",
        }


@dataclass
class TesterEnvironmentDoctor:
    """Read-only environment readiness doctor for the tester release."""

    state_dir: str = ".solaris_ai_nn_live"
    tester_state_dir: str = ".solaris_ai_nn_tester"
    include_dev: bool = False

    def check(self) -> EnvironmentDoctorResult:
        result = EnvironmentDoctorResult()
        H = EnvironmentHealth

        def add(check, health, detail="", required=True):
            result.findings.append(EnvironmentFinding(check, health, detail,
                                                      required))

        # Python.
        add("python_executable", H.PASS, sys.executable or "")
        add("python_version", H.PASS if sys.version_info[:2] >= _MIN_PYTHON
            else H.BLOCKED,
            ".".join(str(v) for v in sys.version_info[:3]))

        # Package + CLI import.
        add("package_import",
            H.PASS if self._importable("solaris_ai_nn") else H.BLOCKED)
        cli_ok = self._importable("solaris_ai_nn.cli")
        add("cli_import", H.PASS if cli_ok else H.BLOCKED)

        # Command registry.
        from .command_registry_check import CommandRegistryCheck
        cmd = CommandRegistryCheck().check()
        add("cli_command_registry",
            H.PASS if cmd.passed else H.BLOCKED,
            f"missing required: {cmd.missing_required}" if not cmd.passed
            else f"{cmd.to_dict()['registered_count']} commands registered")

        # Working dir + write permissions.
        add("current_working_directory", H.PASS, os.getcwd())
        add("tester_state_dir_writable",
            H.PASS if self._writable(self.tester_state_dir) else H.BLOCKED,
            self.tester_state_dir)
        add("live_state_dir_writable",
            H.PASS if self._writable(self.state_dir)
            else H.PASS_WITH_WARNINGS, self.state_dir, required=False)

        # Example fixtures present.
        fixture = os.path.join(
            "examples", "tester_fixture_spine", "fixture_tester_v0",
            "events.jsonl")
        add("example_fixture_files",
            H.PASS if os.path.isfile(fixture) else H.MISSING, fixture)

        # Tester modules available.
        for label, module, required in (
                ("tester_fixture_spine", "solaris_ai_nn.tester_fixture_spine",
                 True),
                ("environmental_membrane",
                 "solaris_ai_nn.environmental_membrane", True),
                ("membrane_integration",
                 "solaris_ai_nn.membrane_integration", True),
                ("tester_console", "solaris_ai_nn.tester_console", True),
                ("tester_feedback", "solaris_ai_nn.tester_feedback", True),
                ("tester_live_readonly",
                 "solaris_ai_nn.tester_live_readonly", True),
                ("pytest", "pytest", False)):
            if module == "pytest" and not self.include_dev:
                continue
            ok = self._importable(module)
            add(f"{label}_available",
                H.PASS if ok else (H.MISSING if required
                                   else H.PASS_WITH_WARNINGS),
                "" if ok else f"{module} not importable", required=required)

        # Live tester templates + docs (warning only; generated on demand).
        gov = os.path.join(
            "examples", "tester_live_readonly",
            "LIVE_READONLY_GOVERNANCE.tester.template.json")
        add("live_tester_templates_present",
            H.PASS if os.path.isfile(gov) else H.PASS_WITH_WARNINGS, gov,
            required=False)
        add("docs_files_present",
            H.PASS if os.path.isfile(os.path.join("docs", "ARCHITECTURE.md"))
            else H.PASS_WITH_WARNINGS, "docs/ARCHITECTURE.md", required=False)

        # ClaimGuard availability.
        add("claim_safety_scan_available",
            H.PASS if self._importable("solaris_ai_nn.governance.compliance")
            else H.PASS_WITH_WARNINGS, "", required=False)
        return result

    @staticmethod
    def _importable(module: str) -> bool:
        try:
            importlib.import_module(module)
            return True
        except Exception:
            return False

    @staticmethod
    def _writable(path: str) -> bool:
        try:
            os.makedirs(path, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=path, delete=True):
                return True
        except Exception:
            return False
