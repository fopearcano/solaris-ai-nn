"""Tester release-candidate profile -- bounded, local, assembly-only config.

:class:`TesterRCProfile` describes a bounded RC assembly run. The default profile
(``tester_rc_v0``) is local and assembly-only: it collects artifacts, builds a manifest,
runs the readiness gate, builds docs (release notes, quickstart, runbook, known issues,
feedback guide), builds the RC checklist, and assembles a local RC bundle. It publishes
nothing, creates no Git releases/tags/issues, uploads no package, runs no shell/network/
browser, executes no artifact contents, and makes no unsupported claims. Open release
blockers block RC readiness; missing membrane blocks live-read-only RC readiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class TesterRCMode:
    TESTER_RC_FULL = "tester_rc_full"
    TESTER_RC_MANIFEST_ONLY = "tester_rc_manifest_only"
    TESTER_RC_DOCS_ONLY = "tester_rc_docs_only"
    TESTER_RC_BUNDLE_ONLY = "tester_rc_bundle_only"
    TESTER_RC_READINESS_ONLY = "tester_rc_readiness_only"
    TESTER_RC_REPORT_ONLY = "tester_rc_report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (TESTER_RC_FULL, TESTER_RC_MANIFEST_ONLY, TESTER_RC_DOCS_ONLY,
           TESTER_RC_BUNDLE_ONLY, TESTER_RC_READINESS_ONLY,
           TESTER_RC_REPORT_ONLY, DOCTOR_ONLY)


class TesterRCConstraint:
    LOCAL_ONLY = "local_only"
    TRUSTED_TESTER_ONLY = "trusted_tester_only"
    NO_PUBLIC_RELEASE = "no_public_release"
    NO_PACKAGE_UPLOAD = "no_package_upload"
    NO_GIT_RELEASE_AUTOMATION = "no_git_github_release_automation"
    NO_TAG_CREATION = "no_tag_creation"
    NO_ISSUE_CREATION = "no_issue_creation"
    NO_NETWORK_SHELL = "no_network_shell_browser_os_git_github"
    NO_HARDWARE = "no_hardware_control"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_BACKGROUND_SERVICE = "no_background_service"
    BOUNDED_RUNTIME = "bounded_runtime"
    FIXTURE_DEMO_REQUIRED = "fixture_demo_required"
    PACKAGING_DOCTOR_REQUIRED = "packaging_doctor_required"
    SAFETY_FREEZE_REQUIRED = "safety_freeze_required"
    OPEN_BLOCKERS_BLOCK = "open_release_blockers_block_rc_readiness"
    MISSING_MEMBRANE_BLOCKS_LIVE = "missing_membrane_blocks_live_readonly_rc"
    FEEDBACK_NON_TRAINING = "tester_feedback_remains_non_training"
    NO_UNSUPPORTED_CLAIMS = "no_unsupported_claims"

    ALL = (LOCAL_ONLY, TRUSTED_TESTER_ONLY, NO_PUBLIC_RELEASE,
           NO_PACKAGE_UPLOAD, NO_GIT_RELEASE_AUTOMATION, NO_TAG_CREATION,
           NO_ISSUE_CREATION, NO_NETWORK_SHELL, NO_HARDWARE, NO_FEEDER_CONTROL,
           NO_BACKGROUND_SERVICE, BOUNDED_RUNTIME, FIXTURE_DEMO_REQUIRED,
           PACKAGING_DOCTOR_REQUIRED, SAFETY_FREEZE_REQUIRED,
           OPEN_BLOCKERS_BLOCK, MISSING_MEMBRANE_BLOCKS_LIVE,
           FEEDBACK_NON_TRAINING, NO_UNSUPPORTED_CLAIMS)


DEFAULT_PROFILE_ID = "tester_rc_v0"


@dataclass
class TesterRCProfile:
    """A bounded, local, assembly-only release-candidate profile."""

    profile_id: str
    purpose: str
    mode: str = TesterRCMode.TESTER_RC_FULL
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 60.0
    collect_artifacts: bool = True
    build_manifest: bool = True
    run_readiness_gate: bool = True
    build_docs: bool = True
    build_checklist: bool = True
    build_bundle: bool = True
    allow_docs_only_rc: bool = False
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in TesterRCMode.ALL:
            self.mode = TesterRCMode.TESTER_RC_FULL
        m = self.mode
        full = (TesterRCMode.TESTER_RC_FULL, TesterRCMode.TESTER_RC_REPORT_ONLY)
        if m not in full:
            self.build_manifest = m in (TesterRCMode.TESTER_RC_MANIFEST_ONLY,
                                        TesterRCMode.TESTER_RC_READINESS_ONLY,
                                        TesterRCMode.TESTER_RC_BUNDLE_ONLY)
            self.collect_artifacts = m in (
                TesterRCMode.TESTER_RC_MANIFEST_ONLY,
                TesterRCMode.TESTER_RC_READINESS_ONLY,
                TesterRCMode.TESTER_RC_BUNDLE_ONLY)
            self.run_readiness_gate = m == TesterRCMode.TESTER_RC_READINESS_ONLY
            self.build_docs = m == TesterRCMode.TESTER_RC_DOCS_ONLY
            self.build_checklist = m == TesterRCMode.TESTER_RC_READINESS_ONLY
            self.build_bundle = m == TesterRCMode.TESTER_RC_BUNDLE_ONLY
            if m == TesterRCMode.DOCTOR_ONLY:
                self.collect_artifacts = self.build_manifest = False
                self.run_readiness_gate = self.build_docs = False
                self.build_checklist = self.build_bundle = False

    @property
    def is_doctor_only(self) -> bool:
        return self.mode == TesterRCMode.DOCTOR_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s,
            "collect_artifacts": self.collect_artifacts,
            "build_manifest": self.build_manifest,
            "run_readiness_gate": self.run_readiness_gate,
            "build_docs": self.build_docs,
            "build_checklist": self.build_checklist,
            "build_bundle": self.build_bundle,
            "allow_docs_only_rc": self.allow_docs_only_rc,
            "local_only": True, "publishes": False, "assembly_only": True,
            "limitations": list(self.limitations),
        }


def default_rc_profile() -> TesterRCProfile:
    """The default local, assembly-only release-candidate profile."""
    return TesterRCProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("assemble the first local trusted-tester release candidate: "
                 "collect docs/reports/manifests, build the RC manifest, run "
                 "the RC readiness gate, build release notes/quickstart/runbook/"
                 "known issues/feedback guide, build the RC checklist, and "
                 "assemble a local RC bundle -- a local assembly step only, not "
                 "a public release"),
        mode=TesterRCMode.TESTER_RC_FULL,
        constraints=list(TesterRCConstraint.ALL),
        max_runtime_s=60.0,
        limitations=[
            "local assembly only; the RC runtime never publishes, uploads, "
            "creates Git releases/tags/issues, or uploads a package",
            "open release blockers block RC readiness; critical safety blockers "
            "cannot be silently waived",
            "missing environmental membrane blocks live-read-only RC readiness",
            "fixture demo, packaging doctor, and safety freeze are required",
            "tester feedback is QA evidence, never training or ground truth",
            "the RC bundle is local; it is shared manually only if a tester "
            "requests it -- nothing is uploaded automatically",
            "this is not a public release, not a product release, and not a "
            "consciousness demo"])


def _profile_for_mode(mode: str) -> TesterRCProfile:
    p = default_rc_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    p.__post_init__()
    purposes = {
        TesterRCMode.TESTER_RC_MANIFEST_ONLY: "build the RC manifest only",
        TesterRCMode.TESTER_RC_DOCS_ONLY:
            "build the RC docs (release notes/quickstart/runbook/known issues/"
            "feedback guide) only",
        TesterRCMode.TESTER_RC_BUNDLE_ONLY: "build the local RC bundle only",
        TesterRCMode.TESTER_RC_READINESS_ONLY: "run the RC readiness gate only",
        TesterRCMode.TESTER_RC_REPORT_ONLY:
            "rebuild RC reports from existing assembly only",
        TesterRCMode.DOCTOR_ONLY: "validate RC prerequisites only",
    }
    if mode in purposes:
        p.purpose = purposes[mode]
    return p


def get_rc_profile(profile_id: Optional[str] = None) -> TesterRCProfile:
    """Return the named profile, defaulting to ``tester_rc_v0``."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_rc_profile()
    for mode in TesterRCMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_rc_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default release-candidate profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in TesterRCMode.ALL]
