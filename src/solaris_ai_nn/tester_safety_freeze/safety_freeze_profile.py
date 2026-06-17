"""Tester safety-freeze profile -- bounded, local, report/gate-only config.

:class:`TesterSafetyFreezeProfile` describes a bounded safety-freeze run. The default
profile (``tester_safety_freeze_v0``) is local and report/gate-only: it scans claims,
capabilities, and artifacts, runs the red-team checklist, and runs the release blocker
gate. It publishes nothing, creates no Git releases/tags/issues, runs no shell/network/
browser, and makes no unsupported claims. Safety blockers must be visible and the
release-blocker count must be explicit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class TesterSafetyFreezeMode:
    TESTER_SAFETY_FREEZE_FULL = "tester_safety_freeze_full"
    TESTER_CLAIM_FREEZE_ONLY = "tester_claim_freeze_only"
    TESTER_CAPABILITY_FREEZE_ONLY = "tester_capability_freeze_only"
    TESTER_RED_TEAM_ONLY = "tester_red_team_only"
    TESTER_RELEASE_BLOCKERS_ONLY = "tester_release_blockers_only"
    TESTER_ARTIFACT_SCAN_ONLY = "tester_artifact_scan_only"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (TESTER_SAFETY_FREEZE_FULL, TESTER_CLAIM_FREEZE_ONLY,
           TESTER_CAPABILITY_FREEZE_ONLY, TESTER_RED_TEAM_ONLY,
           TESTER_RELEASE_BLOCKERS_ONLY, TESTER_ARTIFACT_SCAN_ONLY,
           REPORT_ONLY, DOCTOR_ONLY)


class TesterSafetyFreezeConstraint:
    LOCAL_ONLY = "local_only"
    NO_PUBLISH = "no_publish_upload"
    NO_GIT = "no_git_github"
    NO_ISSUE = "no_issue_creation"
    NO_RELEASE_TAG = "no_release_tag_creation"
    NO_NETWORK_SHELL = "no_shell_network_browser_os_access"
    NO_HARDWARE = "no_hardware_control"
    NO_FEEDER_CONTROL = "no_feeder_control"
    BOUNDED_RUNTIME = "bounded_runtime"
    ARTIFACT_SCAN_ONLY = "artifact_scan_only"
    CLAIM_SCAN_REQUIRED = "claim_scan_required"
    CAPABILITY_SCAN_REQUIRED = "capability_scan_required"
    RELEASE_BLOCKER_GATE_REQUIRED = "release_blocker_gate_required"
    NO_UNSUPPORTED_CLAIMS = "no_unsupported_claims"
    NO_FEEDBACK_TRAINING = "no_feedback_as_training"
    NO_RAW_EVENT_BYPASS = "no_raw_event_bypass"
    NO_MEMBRANE_BYPASS = "no_membrane_bypass"
    SAFETY_BLOCKERS_VISIBLE = "safety_blockers_must_be_visible"
    BLOCKER_COUNT_EXPLICIT = "release_blocker_count_must_be_explicit"

    ALL = (LOCAL_ONLY, NO_PUBLISH, NO_GIT, NO_ISSUE, NO_RELEASE_TAG,
           NO_NETWORK_SHELL, NO_HARDWARE, NO_FEEDER_CONTROL, BOUNDED_RUNTIME,
           ARTIFACT_SCAN_ONLY, CLAIM_SCAN_REQUIRED, CAPABILITY_SCAN_REQUIRED,
           RELEASE_BLOCKER_GATE_REQUIRED, NO_UNSUPPORTED_CLAIMS,
           NO_FEEDBACK_TRAINING, NO_RAW_EVENT_BYPASS, NO_MEMBRANE_BYPASS,
           SAFETY_BLOCKERS_VISIBLE, BLOCKER_COUNT_EXPLICIT)


DEFAULT_PROFILE_ID = "tester_safety_freeze_v0"


@dataclass
class TesterSafetyFreezeProfile:
    """A bounded, local, report/gate-only safety-freeze profile."""

    profile_id: str
    purpose: str
    mode: str = TesterSafetyFreezeMode.TESTER_SAFETY_FREEZE_FULL
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 60.0
    run_claim_freeze: bool = True
    run_capability_freeze: bool = True
    run_artifact_scan: bool = True
    run_red_team: bool = True
    run_release_blocker_gate: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in TesterSafetyFreezeMode.ALL:
            self.mode = TesterSafetyFreezeMode.TESTER_SAFETY_FREEZE_FULL
        m = self.mode
        full = (TesterSafetyFreezeMode.TESTER_SAFETY_FREEZE_FULL,
                TesterSafetyFreezeMode.REPORT_ONLY)
        if m not in full:
            self.run_claim_freeze = m in (
                TesterSafetyFreezeMode.TESTER_CLAIM_FREEZE_ONLY,
                TesterSafetyFreezeMode.TESTER_ARTIFACT_SCAN_ONLY)
            self.run_capability_freeze = m in (
                TesterSafetyFreezeMode.TESTER_CAPABILITY_FREEZE_ONLY,
                TesterSafetyFreezeMode.TESTER_ARTIFACT_SCAN_ONLY)
            self.run_artifact_scan = m == \
                TesterSafetyFreezeMode.TESTER_ARTIFACT_SCAN_ONLY
            self.run_red_team = m == TesterSafetyFreezeMode.TESTER_RED_TEAM_ONLY
            self.run_release_blocker_gate = m in (
                TesterSafetyFreezeMode.TESTER_RELEASE_BLOCKERS_ONLY,)
            if m == TesterSafetyFreezeMode.DOCTOR_ONLY:
                self.run_claim_freeze = self.run_capability_freeze = False
                self.run_artifact_scan = self.run_red_team = False
                self.run_release_blocker_gate = False

    @property
    def is_doctor_only(self) -> bool:
        return self.mode == TesterSafetyFreezeMode.DOCTOR_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s,
            "run_claim_freeze": self.run_claim_freeze,
            "run_capability_freeze": self.run_capability_freeze,
            "run_artifact_scan": self.run_artifact_scan,
            "run_red_team": self.run_red_team,
            "run_release_blocker_gate": self.run_release_blocker_gate,
            "local_only": True, "publishes": False, "report_gate_only": True,
            "limitations": list(self.limitations),
        }


def default_safety_freeze_profile() -> TesterSafetyFreezeProfile:
    """The default local, report/gate-only safety-freeze profile."""
    return TesterSafetyFreezeProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("the tester-release safety firewall: scan local artifacts for "
                 "forbidden claims and unsafe capabilities, run the red-team "
                 "checklist, and run the release blocker gate before a tester "
                 "release candidate -- a report/gate-only layer, not a new "
                 "research layer"),
        mode=TesterSafetyFreezeMode.TESTER_SAFETY_FREEZE_FULL,
        constraints=list(TesterSafetyFreezeConstraint.ALL),
        max_runtime_s=60.0,
        limitations=[
            "report/gate-only; the safety freeze never modifies runtime "
            "behaviour, publishes, or creates releases/tags/issues",
            "it scans only local text artifacts and does not execute them",
            "forbidden consciousness/life/agency claims and unsafe capability "
            "implications block the tester release candidate",
            "membrane bypass and raw-event bypass are release blockers",
            "tester feedback is QA evidence, never training; feedback informs "
            "blocker classification but never modifies safety policy "
            "automatically",
            "the safety freeze does NOT prove the system safe in general; it is "
            "a tester-release gate only"])


def _profile_for_mode(mode: str) -> TesterSafetyFreezeProfile:
    p = default_safety_freeze_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    p.__post_init__()
    purposes = {
        TesterSafetyFreezeMode.TESTER_CLAIM_FREEZE_ONLY:
            "run the forbidden claim scan only",
        TesterSafetyFreezeMode.TESTER_CAPABILITY_FREEZE_ONLY:
            "run the capability freeze scan only",
        TesterSafetyFreezeMode.TESTER_RED_TEAM_ONLY:
            "run the red-team checklist only",
        TesterSafetyFreezeMode.TESTER_RELEASE_BLOCKERS_ONLY:
            "run the release blocker gate only",
        TesterSafetyFreezeMode.TESTER_ARTIFACT_SCAN_ONLY:
            "scan local artifacts for safety/claim issues only",
        TesterSafetyFreezeMode.REPORT_ONLY:
            "rebuild safety freeze reports from existing scans only",
        TesterSafetyFreezeMode.DOCTOR_ONLY:
            "validate safety-freeze prerequisites only",
    }
    if mode in purposes:
        p.purpose = purposes[mode]
    return p


def get_safety_freeze_profile(profile_id: Optional[str] = None,
                              ) -> TesterSafetyFreezeProfile:
    """Return the named profile, defaulting to ``tester_safety_freeze_v0``."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_safety_freeze_profile()
    for mode in TesterSafetyFreezeMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_safety_freeze_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default safety freeze profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in TesterSafetyFreezeMode.ALL]
