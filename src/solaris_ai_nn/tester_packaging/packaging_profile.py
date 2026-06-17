"""Tester packaging profile -- bounded, local, report-only packaging config.

:class:`TesterPackagingProfile` describes a bounded packaging-readiness run. The default
profile (``tester_packaging_v0``) is local and report-only: it installs nothing,
publishes/uploads nothing, creates no Git tags/releases, opens no browser, starts no
background services, and makes no unsupported claims. External feeders remain manual,
tester feedback remains non-training, the fixture demo is required before any live run,
and the membrane is required for the full tester path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class TesterPackagingMode:
    TESTER_PACKAGING_DOCTOR = "tester_packaging_doctor"
    TESTER_PACKAGING_MANIFEST = "tester_packaging_manifest"
    TESTER_PACKAGING_GUIDES = "tester_packaging_guides"
    TESTER_PACKAGING_CLEAN_MACHINE = "tester_packaging_clean_machine"
    TESTER_PACKAGING_FULL = "tester_packaging_full"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (TESTER_PACKAGING_DOCTOR, TESTER_PACKAGING_MANIFEST,
           TESTER_PACKAGING_GUIDES, TESTER_PACKAGING_CLEAN_MACHINE,
           TESTER_PACKAGING_FULL, REPORT_ONLY, DOCTOR_ONLY)


class TesterPackagingConstraint:
    LOCAL_ONLY = "local_only"
    NO_UPLOAD = "no_upload"
    NO_PUBLISH = "no_publish"
    NO_GIT_RELEASE_AUTOMATION = "no_git_github_release_automation"
    NO_TAG_CREATION = "no_tag_creation"
    NO_GLOBAL_INSTALL = "no_global_install"
    NO_BACKGROUND_SERVICES = "no_background_services"
    NO_BROWSER_AUTO_OPEN = "no_browser_auto_open"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    NO_NETWORK_SHELL_GIT = "no_network_shell_browser_os_git_github_from_runtime"
    BOUNDED_RUNTIME = "bounded_runtime"
    NO_UNSUPPORTED_CLAIMS = "no_unsupported_claims"
    FEEDBACK_NOT_TRAINING = "tester_feedback_remains_non_training"
    EXTERNAL_FEEDERS_MANUAL = "external_feeder_scripts_remain_manual"
    FIXTURE_BEFORE_LIVE = "fixture_tester_demo_required_before_live_tester_run"
    MEMBRANE_REQUIRED_FULL = "membrane_required_for_full_tester_path"

    ALL = (LOCAL_ONLY, NO_UPLOAD, NO_PUBLISH, NO_GIT_RELEASE_AUTOMATION,
           NO_TAG_CREATION, NO_GLOBAL_INSTALL, NO_BACKGROUND_SERVICES,
           NO_BROWSER_AUTO_OPEN, NO_FEEDER_CONTROL, NO_HARDWARE_CONTROL,
           NO_NETWORK_SHELL_GIT, BOUNDED_RUNTIME, NO_UNSUPPORTED_CLAIMS,
           FEEDBACK_NOT_TRAINING, EXTERNAL_FEEDERS_MANUAL, FIXTURE_BEFORE_LIVE,
           MEMBRANE_REQUIRED_FULL)


DEFAULT_PROFILE_ID = "tester_packaging_v0"


@dataclass
class TesterPackagingProfile:
    """A bounded, local, report-only tester packaging profile."""

    profile_id: str
    purpose: str
    mode: str = TesterPackagingMode.TESTER_PACKAGING_FULL
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 60.0
    run_dependency_check: bool = True
    run_environment_doctor: bool = True
    run_command_registry_check: bool = True
    build_guides: bool = True
    build_manifest: bool = True
    run_clean_machine_check: bool = True
    build_platform_notes: bool = True
    include_dev_checks: bool = False
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in TesterPackagingMode.ALL:
            self.mode = TesterPackagingMode.TESTER_PACKAGING_FULL
        m = self.mode
        if m in (TesterPackagingMode.TESTER_PACKAGING_DOCTOR,
                 TesterPackagingMode.DOCTOR_ONLY):
            self.build_guides = self.build_manifest = False
            self.run_clean_machine_check = self.build_platform_notes = False
        elif m == TesterPackagingMode.TESTER_PACKAGING_MANIFEST:
            self.build_guides = self.run_clean_machine_check = False
            self.build_platform_notes = False
        elif m == TesterPackagingMode.TESTER_PACKAGING_GUIDES:
            self.build_manifest = self.run_clean_machine_check = False
        elif m == TesterPackagingMode.TESTER_PACKAGING_CLEAN_MACHINE:
            self.build_guides = self.build_manifest = False
        elif m == TesterPackagingMode.REPORT_ONLY:
            self.build_guides = self.build_manifest = False
            self.build_platform_notes = False

    @property
    def is_doctor_only(self) -> bool:
        return self.mode in (TesterPackagingMode.TESTER_PACKAGING_DOCTOR,
                             TesterPackagingMode.DOCTOR_ONLY)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s,
            "run_dependency_check": self.run_dependency_check,
            "run_environment_doctor": self.run_environment_doctor,
            "run_command_registry_check": self.run_command_registry_check,
            "build_guides": self.build_guides,
            "build_manifest": self.build_manifest,
            "run_clean_machine_check": self.run_clean_machine_check,
            "build_platform_notes": self.build_platform_notes,
            "include_dev_checks": self.include_dev_checks,
            "local_only": True, "installs_packages": False, "publishes": False,
            "limitations": list(self.limitations),
        }


def default_packaging_profile() -> TesterPackagingProfile:
    """The default local, report-only tester packaging profile."""
    return TesterPackagingProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("a bounded, local, report-only packaging-readiness run: check "
                 "dependencies, run the environment doctor, verify the tester "
                 "command registry, build install guides + quickstart + "
                 "troubleshooting, build the release artifact manifest, run the "
                 "clean-machine readiness check, and write platform notes -- it "
                 "installs nothing, publishes nothing, and creates no releases/"
                 "tags"),
        mode=TesterPackagingMode.TESTER_PACKAGING_FULL,
        constraints=list(TesterPackagingConstraint.ALL),
        max_runtime_s=60.0,
        limitations=[
            "local report-only; the runtime never installs packages, "
            "publishes/uploads, or creates Git releases/tags/issues",
            "the environment doctor reports readiness; it never auto-fixes, runs "
            "shell, accesses the network, opens a browser, or installs anything",
            "external feeders remain manual; tester feedback remains "
            "non-training",
            "the fixture tester demo is required before any live-read-only run; "
            "the environmental membrane is required for the full tester path",
            "clean-machine readiness flags hidden developer-machine assumptions",
            "packaging readiness is a local assessment, not a public release, "
            "and not evidence of consciousness/life/agency"])


def _profile_for_mode(mode: str) -> TesterPackagingProfile:
    p = default_packaging_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    p.__post_init__()
    purposes = {
        TesterPackagingMode.TESTER_PACKAGING_DOCTOR:
            "run the environment doctor + command registry check only",
        TesterPackagingMode.TESTER_PACKAGING_MANIFEST:
            "build the release artifact manifest only",
        TesterPackagingMode.TESTER_PACKAGING_GUIDES:
            "build the install guides + quickstart + troubleshooting only",
        TesterPackagingMode.TESTER_PACKAGING_CLEAN_MACHINE:
            "run the clean-machine readiness check only",
        TesterPackagingMode.REPORT_ONLY:
            "rebuild packaging reports from existing checks only",
        TesterPackagingMode.DOCTOR_ONLY:
            "validate packaging prerequisites only",
    }
    if mode in purposes:
        p.purpose = purposes[mode]
    return p


def get_packaging_profile(profile_id: Optional[str] = None,
                          ) -> TesterPackagingProfile:
    """Return the named profile, defaulting to ``tester_packaging_v0``."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_packaging_profile()
    for mode in TesterPackagingMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_packaging_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default tester packaging profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in TesterPackagingMode.ALL]
