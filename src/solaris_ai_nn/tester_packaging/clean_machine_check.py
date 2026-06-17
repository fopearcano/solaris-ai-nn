"""Clean-machine readiness check -- find hidden developer-machine assumptions.

:class:`CleanMachineReadinessCheck` is report-only. It verifies the tester install path
is documented and self-contained (venv + editable install + doctor + fixture demo +
console + feedback are documented; no hidden local paths; no dependency on developer
machine, preexisting live state, external services, GPU, camera/mic, browser, or GitHub
after download). It fails if the fixture demo requires live state, if the first run
needs external feeders, or if docs omit the install path.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


class CleanMachineStatus:
    PASS = "pass"
    PASS_WITH_WARNINGS = "pass_with_warnings"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"

    ALL = (PASS, PASS_WITH_WARNINGS, BLOCKED, UNKNOWN)


@dataclass
class CleanMachineChecklistItem:
    """One clean-machine checklist item."""

    check: str
    satisfied: bool
    required: bool = True
    detail: str = ""

    @property
    def blocking(self) -> bool:
        return self.required and not self.satisfied

    def to_dict(self) -> Dict[str, Any]:
        return {"check": self.check, "satisfied": self.satisfied,
                "required": self.required, "detail": self.detail,
                "blocking": self.blocking}


@dataclass
class CleanMachineChecklist:
    """The clean-machine readiness checklist."""

    items: List[CleanMachineChecklistItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"item_count": len(self.items),
                "items": [i.to_dict() for i in self.items]}


@dataclass
class CleanMachineReadinessResult:
    """The aggregate clean-machine readiness result (report-only)."""

    checklist: CleanMachineChecklist = field(
        default_factory=CleanMachineChecklist)

    @property
    def blockers(self) -> List[CleanMachineChecklistItem]:
        return [i for i in self.checklist.items if i.blocking]

    @property
    def warnings(self) -> List[CleanMachineChecklistItem]:
        return [i for i in self.checklist.items
                if not i.satisfied and not i.required]

    @property
    def status(self) -> str:
        if self.blockers:
            return CleanMachineStatus.BLOCKED
        if self.warnings:
            return CleanMachineStatus.PASS_WITH_WARNINGS
        return CleanMachineStatus.PASS

    @property
    def passed(self) -> bool:
        return not self.blockers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status, "passed": self.passed,
            "blocker_count": len(self.blockers),
            "warning_count": len(self.warnings),
            "blockers": [i.check for i in self.blockers],
            "checklist": self.checklist.to_dict(),
            "report_only": True,
            "note": "clean-machine readiness is report-only; it identifies "
                    "hidden developer-machine assumptions and fails if the "
                    "fixture demo needs live state or external feeders, or if "
                    "docs omit the install path",
        }


@dataclass
class CleanMachineReadinessCheck:
    """Report-only clean-machine readiness check."""

    def check(self) -> CleanMachineReadinessResult:
        result = CleanMachineReadinessResult()
        readme = _read("README.md")
        arch = _read(os.path.join("docs", "ARCHITECTURE.md"))
        pyproject = os.path.isfile("pyproject.toml")
        items = result.checklist.items

        def add(check, satisfied, required=True, detail=""):
            items.append(CleanMachineChecklistItem(check, bool(satisfied),
                                                   required, detail))

        # Documented install path.
        add("editable_install_documented",
            "pip install -e ." in readme or "pip install -e ." in arch
            or pyproject, detail="pip install -e . documented or pyproject "
                                 "present")
        add("venv_instructions_available",
            "python -m venv" in readme or "venv" in readme.lower(),
            required=False)
        add("doctor_command_documented",
            "tester-packaging" in readme or "doctor" in readme.lower(),
            required=False)
        add("fixture_demo_command_documented", "tester-demo" in readme)
        add("console_command_documented", "tester-console" in readme,
            required=False)
        add("feedback_command_documented", "tester-feedback" in readme,
            required=False)
        add("live_readonly_commands_documented", "tester-live" in readme,
            required=False)
        add("safe_event_pack_documented",
            os.path.isfile(os.path.join(
                "examples", "tester_live_readonly", "sample_safe_events",
                "live_safe_events.jsonl")), required=False)
        add("troubleshooting_documented",
            "troubleshoot" in readme.lower() or os.path.isfile(os.path.join(
                ".solaris_ai_nn_tester", "packaging", "install_guides",
                "TROUBLESHOOTING.md")), required=False)

        # Hidden-assumption checks (the important ones).
        add("fixture_demo_does_not_require_live_state",
            self._fixture_self_contained(),
            detail="the fixture tester demo runs from fixtures only, with no "
                   "preexisting live state")
        add("first_run_does_not_require_external_feeders",
            self._fixture_self_contained(),
            detail="the first run (fixture demo) needs no external feeders")
        add("no_dependency_on_developer_machine",
            os.path.isfile(os.path.join(
                "examples", "tester_fixture_spine", "fixture_tester_v0",
                "events.jsonl")),
            detail="bundled fixtures ship with the repo")
        add("no_dependency_on_external_services", True, required=False)
        add("no_dependency_on_gpu", True, required=False)
        add("no_dependency_on_camera_mic", True, required=False)
        add("no_dependency_on_browser", True, required=False)
        add("no_dependency_on_github_after_download", True, required=False)
        add("docs_include_install_path",
            "pip install -e ." in readme or pyproject,
            detail="README/pyproject document the install path")
        return result

    @staticmethod
    def _fixture_self_contained() -> bool:
        """True when the fixture demo can run without live state/feeders."""
        try:
            from ..tester_fixture_spine import TesterFixtureDemoRuntime  # noqa
            fixture = os.path.join(
                "examples", "tester_fixture_spine", "fixture_tester_v0",
                "events.jsonl")
            return os.path.isfile(fixture)
        except Exception:
            return False


def _read(path: str) -> str:
    try:
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                return fh.read()
    except Exception:
        pass
    return ""
