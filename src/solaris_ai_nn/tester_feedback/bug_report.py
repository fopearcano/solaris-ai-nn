"""Tester bug report -- local bug evidence for developer review (no auto-fix).

A bug report is local evidence only: it patches nothing, triggers no automatic fix, and
creates no GitHub issue.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


class BugAffectedModule:
    INSTALL = "install"
    DOCTOR = "doctor"
    TESTER_FIXTURE = "tester_fixture"
    GOLDEN_MANIFEST = "golden_manifest"
    REPRODUCIBILITY = "reproducibility"
    REGRESSION = "regression"
    TESTER_LIVE_INIT = "tester_live_init"
    LIVE_DOCTOR = "live_doctor"
    FEEDER_TEMPLATES = "feeder_templates"
    SAFE_EVENT_PACK = "safe_event_pack"
    LIVE_BIRTH = "live_birth"
    MEMBRANE = "membrane"
    MEMBRANE_INTEGRATION = "membrane_integration"
    OBSERVATION = "observation"
    TESTER_CONSOLE = "tester_console"
    FEEDBACK_SYSTEM = "feedback_system"
    DOCS = "docs"
    UNKNOWN = "unknown"

    ALL = (INSTALL, DOCTOR, TESTER_FIXTURE, GOLDEN_MANIFEST, REPRODUCIBILITY,
           REGRESSION, TESTER_LIVE_INIT, LIVE_DOCTOR, FEEDER_TEMPLATES,
           SAFE_EVENT_PACK, LIVE_BIRTH, MEMBRANE, MEMBRANE_INTEGRATION,
           OBSERVATION, TESTER_CONSOLE, FEEDBACK_SYSTEM, DOCS, UNKNOWN)


@dataclass
class TesterBugReport:
    """A local bug report (developer review evidence; patches nothing)."""

    bug_id: str
    run_id: str = ""
    affected_command: str = ""
    affected_module: str = BugAffectedModule.UNKNOWN
    expected_behavior: str = ""
    actual_behavior: str = ""
    reproduction_steps: List[str] = field(default_factory=list)
    error_message: str = ""
    artifact_paths: List[str] = field(default_factory=list)
    blocker_severity: str = "unknown"
    workaround: str = ""
    privacy_check_passed: bool = True
    non_training_acknowledgement: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_type": "bug_report", "bug_id": self.bug_id,
            "run_id": self.run_id, "affected_command": self.affected_command,
            "affected_module": self.affected_module,
            "expected_behavior": self.expected_behavior,
            "actual_behavior": self.actual_behavior,
            "reproduction_steps": list(self.reproduction_steps),
            "error_message": self.error_message,
            "artifact_paths": list(self.artifact_paths),
            "blocker_severity": self.blocker_severity,
            "workaround": self.workaround,
            "privacy_check_passed": self.privacy_check_passed,
            "non_training_acknowledgement": self.non_training_acknowledgement,
            "patches_anything": False, "triggers_auto_fix": False,
            "creates_github_issue": False,
        }


@dataclass
class BugReportValidationResult:
    """The result of validating a bug report."""

    valid: bool
    findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.valid, "findings": list(self.findings)}


@dataclass
class BugReportBuilder:
    """Builds and validates bug reports from local feedback dicts."""

    def build(self, data: Dict[str, Any]) -> TesterBugReport:
        steps = data.get("reproduction_steps", [])
        if isinstance(steps, str):
            steps = [s.strip() for s in steps.splitlines() if s.strip()]
        paths = data.get("artifact_paths", [])
        if isinstance(paths, str):
            paths = [paths] if paths else []
        module = str(data.get("affected_module", BugAffectedModule.UNKNOWN))
        if module not in BugAffectedModule.ALL:
            module = BugAffectedModule.UNKNOWN
        return TesterBugReport(
            bug_id=str(data.get("bug_id") or data.get("feedback_id")
                       or f"bug_{int(time.time() * 1000)}"),
            run_id=str(data.get("run_id", "")),
            affected_command=str(data.get("affected_command",
                                          data.get("command_run", ""))),
            affected_module=module,
            expected_behavior=str(data.get("expected_behavior", "")),
            actual_behavior=str(data.get("actual_behavior", "")),
            reproduction_steps=list(steps),
            error_message=str(data.get("error_message", "")),
            artifact_paths=[str(p) for p in paths],
            blocker_severity=str(data.get("blocker_severity",
                                          data.get("severity", "unknown"))),
            workaround=str(data.get("workaround", "")),
            privacy_check_passed=bool(data.get("privacy_check_passed", True)),
            non_training_acknowledgement=bool(
                data.get("non_training_acknowledgement", False)))

    def validate(self, report: TesterBugReport) -> BugReportValidationResult:
        findings: List[str] = []
        if not report.actual_behavior:
            findings.append("actual_behavior is empty")
        if not report.non_training_acknowledgement:
            findings.append("non_training_acknowledgement not set")
        return BugReportValidationResult(valid=not findings, findings=findings)
