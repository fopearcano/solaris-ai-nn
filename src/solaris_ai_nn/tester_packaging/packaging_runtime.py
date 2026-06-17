"""Tester packaging runtime -- bounded, local, report-only packaging readiness.

:class:`TesterPackagingRuntime` runs the dependency check, environment doctor, and
command registry check; builds the install guides, quickstart, troubleshooting,
platform notes, and release manifest; and runs the clean-machine readiness check. It
writes packaging docs/reports only. It installs nothing, publishes/uploads nothing,
creates no Git tags/releases, opens no browser, starts no background services, runs no
shell, accesses no network, controls no feeders/hardware, and makes no unsupported
claims.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .clean_machine_check import CleanMachineReadinessCheck
from .command_registry_check import CommandRegistryCheck
from .dependency_check import DependencyCheck
from .environment_doctor import TesterEnvironmentDoctor
from .install_guide_builder import TesterInstallGuideBuilder
from .packaging_profile import get_packaging_profile
from .platform_notes import PlatformNotesBuilder
from .release_manifest import ReleaseManifestBuilder
from .safety import TesterPackagingSafetyValidator


@dataclass
class TesterPackagingRuntime:
    """Bounded, local, report-only tester packaging runtime."""

    state_dir: str = ".solaris_ai_nn_live"
    tester_state_dir: str = ".solaris_ai_nn_tester"
    packaging_dir: str = ""
    profile: Optional[str] = None
    max_runtime_s: float = 60.0
    strict: bool = False
    dry_run: bool = False
    report_only: bool = False
    guides_only: bool = False
    manifest_only: bool = False
    doctor_only: bool = False
    include_dev_checks: bool = False
    require_claimguard: bool = False

    safety: TesterPackagingSafetyValidator = field(
        default_factory=TesterPackagingSafetyValidator, init=False)
    packaging_profile: Any = field(default=None, init=False)
    run_id: str = field(default="", init=False)
    dependency_result: Any = field(default=None, init=False)
    doctor_result: Any = field(default=None, init=False)
    command_result: Any = field(default=None, init=False)
    clean_machine_result: Any = field(default=None, init=False)
    manifest: Any = field(default=None, init=False)
    guide_paths: Dict[str, str] = field(default_factory=dict, init=False)
    platform_paths: Dict[str, str] = field(default_factory=dict, init=False)
    reports: Dict[str, Any] = field(default_factory=dict, init=False)
    blockers: List[str] = field(default_factory=list, init=False)
    warnings: List[str] = field(default_factory=list, init=False)
    _refused: bool = field(default=False, init=False)

    _SUBDIRS = ("reports", "manifests", "checks", "install_guides", "platforms",
                "index")

    def __post_init__(self) -> None:
        self.packaging_profile = get_packaging_profile(self.profile)
        if not self.packaging_dir:
            self.packaging_dir = os.path.join(self.tester_state_dir, "packaging")
        self.run_id = f"packaging_{int(time.time() * 1000)}"
        if not self.max_runtime_s:
            self._refused = True

    def initialize(self) -> Dict[str, Any]:
        created = []
        for sub in self._SUBDIRS:
            path = os.path.join(self.packaging_dir, sub)
            existed = os.path.isdir(path)
            os.makedirs(path, exist_ok=True)
            created.append({"name": sub, "existed": existed})
        return {"packaging_dir": self.packaging_dir, "directories": created,
                "installs_packages": False, "modifies_environment": False}

    def run_doctor(self) -> Dict[str, Any]:
        self.dependency_result = DependencyCheck(
            include_dev=self.include_dev_checks).check()
        self.doctor_result = TesterEnvironmentDoctor(
            state_dir=self.state_dir, tester_state_dir=self.tester_state_dir,
            include_dev=self.include_dev_checks).check()
        self.command_result = CommandRegistryCheck().check()
        return self.environment_doctor_status()

    def run(self) -> Dict[str, Any]:
        if self._refused or not self.safety.validate_bounded(
                self.max_runtime_s).safe:
            return {"refused": True, "reason": "unbounded runtime"}
        self.initialize()
        p = self.packaging_profile

        if p.run_dependency_check:
            self.dependency_result = DependencyCheck(
                include_dev=self.include_dev_checks).check()
        if p.run_environment_doctor:
            self.doctor_result = TesterEnvironmentDoctor(
                state_dir=self.state_dir,
                tester_state_dir=self.tester_state_dir,
                include_dev=self.include_dev_checks).check()
        if p.run_command_registry_check:
            self.command_result = CommandRegistryCheck().check()
        if p.run_clean_machine_check:
            self.clean_machine_result = CleanMachineReadinessCheck().check()

        if not self.dry_run:
            if p.build_guides:
                self.guide_paths = TesterInstallGuideBuilder().write(
                    os.path.join(self.packaging_dir, "install_guides"))
            if p.build_platform_notes:
                self.platform_paths = PlatformNotesBuilder().write(
                    os.path.join(self.packaging_dir, "platforms"))
            if p.build_manifest:
                self.manifest = ReleaseManifestBuilder().build()
                ReleaseManifestBuilder().write(
                    os.path.join(self.packaging_dir, "manifests"))
            self._build_reports()

        self._collect_blockers()
        if self.require_claimguard and not _claimguard_available():
            self.warnings.append("ClaimGuard required but unavailable")
        self._update_integrations()
        return self._result()

    # -- helpers ------------------------------------------------------------

    def _collect_blockers(self) -> None:
        if self.dependency_result and not self.dependency_result.passed:
            self.blockers.extend(f"dependency: {f.name}"
                                 for f in self.dependency_result.blockers)
            if not self.dependency_result.python_ok:
                self.blockers.append("python version below 3.11")
        if self.command_result and not self.command_result.passed:
            self.blockers.extend(f"missing command: {c}"
                                 for c in self.command_result.missing_required)
        if self.doctor_result and not self.doctor_result.passed:
            self.blockers.extend(f"environment: {f.check}"
                                 for f in self.doctor_result.blockers)
        if self.clean_machine_result and not self.clean_machine_result.passed:
            self.blockers.extend(f"clean-machine: {i.check}"
                                 for i in self.clean_machine_result.blockers)

    def _build_reports(self) -> None:
        from .reports import TesterPackagingReportBuilder
        self.reports = TesterPackagingReportBuilder(self).write()

    def _update_integrations(self) -> None:
        try:
            from ..inner_map.model import InnerMapModel  # noqa: F401
            self._inner_map_record = self.inner_map_record()
        except Exception:
            self.warnings.append("inner map unavailable (record skipped)")

    # -- views --------------------------------------------------------------

    def environment_doctor_status(self) -> Dict[str, Any]:
        dep = self.dependency_result.to_dict() if self.dependency_result else {}
        doc = self.doctor_result.to_dict() if self.doctor_result else {}
        cmd = self.command_result.to_dict() if self.command_result else {}
        return {
            "packaging_run_id": self.run_id,
            "doctor_health": doc.get("overall_health", "unknown"),
            "doctor_passed": doc.get("passed", False),
            "dependency_passed": dep.get("passed", False),
            "dependency_blocker_count": dep.get("blocker_count", 0),
            "command_passed": cmd.get("passed", False),
            "missing_required_command_count": cmd.get(
                "missing_required_count", 0),
            "missing_required_commands": cmd.get("missing_required", []),
        }

    def _safety_freeze_status(self) -> Dict[str, Any]:
        """Read-only view of the tester safety-freeze manifest, if present."""
        import json
        manifest = os.path.join(self.tester_state_dir, "safety_freeze",
                                "manifests", "TESTER_SAFETY_FREEZE_MANIFEST.json")
        if not os.path.isfile(manifest):
            return {"safety_freeze_available": False,
                    "open_release_blocker_count": 0, "readiness": "unknown"}
        try:
            with open(manifest, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return {"safety_freeze_available": False,
                    "open_release_blocker_count": 0, "readiness": "unknown"}
        return {
            "safety_freeze_available": True,
            "latest_safety_freeze_report_path": os.path.join(
                self.tester_state_dir, "safety_freeze", "reports",
                "TESTER_SAFETY_FREEZE_REPORT.md"),
            "open_release_blocker_count": data.get("release_blocker_count", 0),
            "forbidden_claim_count": data.get("forbidden_claim_count", 0),
            "readiness": data.get("readiness", "unknown"),
        }

    def packaging_status(self) -> Dict[str, Any]:
        dep = self.dependency_result.to_dict() if self.dependency_result else {}
        doc = self.doctor_result.to_dict() if self.doctor_result else {}
        cmd = self.command_result.to_dict() if self.command_result else {}
        clean = self.clean_machine_result.to_dict() \
            if self.clean_machine_result else {}
        manifest = self.manifest.to_dict() if self.manifest else {}
        sf = self._safety_freeze_status()
        readiness = "blocked" if (self.blockers
                                  or sf.get("open_release_blocker_count")) else (
            "ready_with_warnings" if (self.warnings or dep.get("warning_count")
                                      or cmd.get("missing_optional_count"))
            else "ready")
        return {
            "packaging_available": True,
            "packaging_run_id": self.run_id,
            "packaging_profile": self.packaging_profile.profile_id,
            "local_only": True, "installs_packages": False, "publishes": False,
            "readiness": readiness,
            "safety_freeze": sf,
            "doctor_status": doc.get("overall_health", "unknown"),
            "doctor_pass": doc.get("passed", False),
            "dependency_blocker_count": dep.get("blocker_count", 0),
            "dependency_warning_count": dep.get("warning_count", 0),
            "missing_required_command_count": cmd.get(
                "missing_required_count", 0),
            "missing_optional_command_count": cmd.get(
                "missing_optional_count", 0),
            "clean_machine_status": clean.get("status", "unknown"),
            "clean_machine_pass": clean.get("passed", False),
            "release_readiness": manifest.get("readiness", "unknown"),
            "blocker_count": len(self.blockers),
            "warning_count": len(self.warnings),
            "latest_packaging_report_path": self.reports.get("markdown"),
            "latest_install_guide_path": self.guide_paths.get("install_guide"),
            "latest_release_manifest_path": os.path.join(
                self.packaging_dir, "manifests",
                "TESTER_RELEASE_ARTIFACT_MANIFEST.json")
            if self.manifest else None,
            "packaging_safety_block_count": self.safety.rejected_count,
        }

    def snapshot(self) -> Dict[str, Any]:
        return self.packaging_status()

    def inner_map_record(self) -> Dict[str, Any]:
        st = self.packaging_status()
        return {
            "packaging_run_id": self.run_id,
            "doctor_status": st["doctor_status"],
            "dependency_blocker_count": st["dependency_blocker_count"],
            "command_blocker_count": st["missing_required_command_count"],
            "clean_machine_readiness": st["clean_machine_status"],
            "latest_install_guide_path": st["latest_install_guide_path"],
            "latest_release_manifest_path": st["latest_release_manifest_path"],
            "local_only": True, "installs_packages": False,
        }

    def recommended_next_actions(self) -> List[str]:
        actions: List[str] = []
        if self.dependency_result and not self.dependency_result.passed:
            actions.append("Install required dependencies: `pip install -e .` "
                           "in an active venv.")
        if self.command_result and not self.command_result.passed:
            actions.append("Reinstall the package so all tester commands "
                           "register (`pip install -e .`).")
        if self.clean_machine_result and not self.clean_machine_result.passed:
            actions.append("Resolve the clean-machine readiness blockers before "
                           "sharing with testers.")
        if not actions:
            actions.append("Run the fixture demo: `python -m solaris_ai_nn "
                           "tester-demo --profile fixture_tester_v0`.")
        return actions

    def _run_summary(self) -> Dict[str, Any]:
        return {
            "packaging_run_id": self.run_id,
            "packaging_profile": self.packaging_profile.to_dict(),
            "packaging_status": self.packaging_status(),
            "dependency_check": self.dependency_result.to_dict()
            if self.dependency_result else {},
            "environment_doctor": self.doctor_result.to_dict()
            if self.doctor_result else {},
            "command_registry": self.command_result.to_dict()
            if self.command_result else {},
            "clean_machine": self.clean_machine_result.to_dict()
            if self.clean_machine_result else {},
            "release_manifest": self.manifest.to_dict() if self.manifest else {},
            "guide_paths": self.guide_paths,
            "platform_paths": self.platform_paths,
            "blockers": list(self.blockers), "warnings": list(self.warnings),
            "next_actions": self.recommended_next_actions(),
            "safety_status": self.safety.snapshot(),
        }

    def _result(self) -> Dict[str, Any]:
        st = self.packaging_status()
        return {
            "refused": False, "run_id": self.run_id,
            "packaging_profile": st["packaging_profile"],
            "readiness": st["readiness"],
            "doctor_status": st["doctor_status"],
            "dependency_blocker_count": st["dependency_blocker_count"],
            "missing_required_command_count": st[
                "missing_required_command_count"],
            "clean_machine_status": st["clean_machine_status"],
            "release_readiness": st["release_readiness"],
            "blocked": bool(self.blockers),
            "blockers": list(self.blockers), "warnings": list(self.warnings),
            "latest_packaging_report_path": st["latest_packaging_report_path"],
            "latest_install_guide_path": st["latest_install_guide_path"],
            "latest_release_manifest_path": st["latest_release_manifest_path"],
            "next_actions": self.recommended_next_actions(),
        }


def _claimguard_available() -> bool:
    try:
        from ..governance.compliance import ClaimGuard  # noqa: F401
        return True
    except Exception:
        return False
