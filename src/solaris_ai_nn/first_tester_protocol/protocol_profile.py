"""First tester protocol profile -- bounded, local, documentation-only config.

:class:`FirstTesterProtocolProfile` describes a bounded protocol-generation run. The
default profile (``first_tester_protocol_v0``) is local and documentation-only: it
generates the session script, acceptance criteria, stop conditions, task sheet, handoff
guide, and post-test review template. It runs no tester session, publishes nothing,
creates no Git releases/tags/issues, and makes no unsupported claims. The fixture demo
comes before live-read-only; live-read-only is optional and governance-gated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class FirstTesterProtocolMode:
    FIRST_TESTER_PROTOCOL_FULL = "first_tester_protocol_full"
    FIRST_TESTER_SCRIPT_ONLY = "first_tester_script_only"
    FIRST_TESTER_ACCEPTANCE_ONLY = "first_tester_acceptance_only"
    FIRST_TESTER_HANDOFF_ONLY = "first_tester_handoff_only"
    FIRST_TESTER_REVIEW_ONLY = "first_tester_review_only"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (FIRST_TESTER_PROTOCOL_FULL, FIRST_TESTER_SCRIPT_ONLY,
           FIRST_TESTER_ACCEPTANCE_ONLY, FIRST_TESTER_HANDOFF_ONLY,
           FIRST_TESTER_REVIEW_ONLY, REPORT_ONLY, DOCTOR_ONLY)


class FirstTesterProtocolConstraint:
    TRUSTED_TESTER_ONLY = "trusted_tester_only"
    LOCAL_ONLY = "local_only_testing"
    RC_BUNDLE_REQUIRED = "rc_bundle_required"
    SAFETY_FREEZE_REQUIRED = "safety_freeze_required"
    PACKAGING_DOCTOR_REQUIRED = "packaging_doctor_required"
    FIXTURE_FIRST_REQUIRED = "fixture_first_required"
    LIVE_READONLY_OPTIONAL = "live_readonly_optional"
    GOVERNANCE_REQUIRED_FOR_LIVE = "governance_required_for_live_readonly"
    EXTERNAL_FEEDERS_MANUAL_ONLY = "external_feeders_manual_only"
    NO_PUBLIC_RELEASE = "no_public_release"
    NO_UPLOAD_PUBLISH = "no_upload_publish"
    NO_GIT_AUTOMATION = "no_git_github_automation"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE = "no_hardware_control"
    NO_NETWORK_SHELL = "no_network_shell_browser_os_access"
    FEEDBACK_NON_TRAINING = "tester_feedback_remains_non_training"
    SAFETY_BLOCKERS_STOP = "safety_blockers_stop_the_session"
    UNSUPPORTED_CLAIMS_STOP = "unsupported_claims_stop_release_progression"
    NO_UNSUPPORTED_CLAIMS = "no_unsupported_consciousness_life_agency_claims"

    ALL = (TRUSTED_TESTER_ONLY, LOCAL_ONLY, RC_BUNDLE_REQUIRED,
           SAFETY_FREEZE_REQUIRED, PACKAGING_DOCTOR_REQUIRED,
           FIXTURE_FIRST_REQUIRED, LIVE_READONLY_OPTIONAL,
           GOVERNANCE_REQUIRED_FOR_LIVE, EXTERNAL_FEEDERS_MANUAL_ONLY,
           NO_PUBLIC_RELEASE, NO_UPLOAD_PUBLISH, NO_GIT_AUTOMATION,
           NO_FEEDER_CONTROL, NO_HARDWARE, NO_NETWORK_SHELL,
           FEEDBACK_NON_TRAINING, SAFETY_BLOCKERS_STOP,
           UNSUPPORTED_CLAIMS_STOP, NO_UNSUPPORTED_CLAIMS)


DEFAULT_PROFILE_ID = "first_tester_protocol_v0"


@dataclass
class FirstTesterProtocolProfile:
    """A bounded, local, documentation-only first-tester protocol profile."""

    profile_id: str
    purpose: str
    mode: str = FirstTesterProtocolMode.FIRST_TESTER_PROTOCOL_FULL
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 60.0
    fixture_first: bool = True
    live_readonly_optional: bool = True
    generate_script: bool = True
    generate_acceptance: bool = True
    generate_stop_conditions: bool = True
    generate_task_sheet: bool = True
    generate_handoff: bool = True
    generate_review: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in FirstTesterProtocolMode.ALL:
            self.mode = FirstTesterProtocolMode.FIRST_TESTER_PROTOCOL_FULL
        m = self.mode
        full = (FirstTesterProtocolMode.FIRST_TESTER_PROTOCOL_FULL,
                FirstTesterProtocolMode.REPORT_ONLY)
        if m not in full:
            self.generate_script = m == \
                FirstTesterProtocolMode.FIRST_TESTER_SCRIPT_ONLY
            self.generate_acceptance = m == \
                FirstTesterProtocolMode.FIRST_TESTER_ACCEPTANCE_ONLY
            self.generate_stop_conditions = m in (
                FirstTesterProtocolMode.FIRST_TESTER_SCRIPT_ONLY,
                FirstTesterProtocolMode.FIRST_TESTER_ACCEPTANCE_ONLY)
            self.generate_task_sheet = m == \
                FirstTesterProtocolMode.FIRST_TESTER_SCRIPT_ONLY
            self.generate_handoff = m == \
                FirstTesterProtocolMode.FIRST_TESTER_HANDOFF_ONLY
            self.generate_review = m == \
                FirstTesterProtocolMode.FIRST_TESTER_REVIEW_ONLY
            if m == FirstTesterProtocolMode.DOCTOR_ONLY:
                self.generate_script = self.generate_acceptance = False
                self.generate_stop_conditions = self.generate_task_sheet = False
                self.generate_handoff = self.generate_review = False

    @property
    def is_doctor_only(self) -> bool:
        return self.mode == FirstTesterProtocolMode.DOCTOR_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s,
            "fixture_first": self.fixture_first,
            "live_readonly_optional": self.live_readonly_optional,
            "generate_script": self.generate_script,
            "generate_acceptance": self.generate_acceptance,
            "generate_stop_conditions": self.generate_stop_conditions,
            "generate_task_sheet": self.generate_task_sheet,
            "generate_handoff": self.generate_handoff,
            "generate_review": self.generate_review,
            "local_only": True, "publishes": False,
            "documentation_only": True, "runs_session": False,
            "limitations": list(self.limitations),
        }


def default_protocol_profile() -> FirstTesterProtocolProfile:
    """The default local, documentation-only first-tester protocol profile."""
    return FirstTesterProtocolProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("define the first trusted-tester protocol: generate the "
                 "session script, acceptance criteria, stop conditions, task "
                 "sheet, artifact handoff guide, and post-test review template "
                 "-- a local, documentation-only layer that never runs the "
                 "tester session"),
        mode=FirstTesterProtocolMode.FIRST_TESTER_PROTOCOL_FULL,
        constraints=list(FirstTesterProtocolConstraint.ALL),
        max_runtime_s=60.0,
        limitations=[
            "documentation-only; the protocol never runs the tester session, "
            "installs packages, publishes, or creates releases/tags/issues",
            "the fixture demo comes before live-read-only; live-read-only is "
            "optional and governance-gated",
            "external feeders are manual; Solaris never starts/controls them",
            "tester feedback is QA evidence, never training or ground truth",
            "stop conditions override curiosity; safety blockers stop the "
            "session and are never worked around",
            "this is not a public release, not a product launch, and not a "
            "consciousness demo"])


def _profile_for_mode(mode: str) -> FirstTesterProtocolProfile:
    p = default_protocol_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    p.__post_init__()
    purposes = {
        FirstTesterProtocolMode.FIRST_TESTER_SCRIPT_ONLY:
            "generate the first-tester session script (and stop conditions/"
            "task sheet) only",
        FirstTesterProtocolMode.FIRST_TESTER_ACCEPTANCE_ONLY:
            "generate the first-tester acceptance criteria only",
        FirstTesterProtocolMode.FIRST_TESTER_HANDOFF_ONLY:
            "generate the first-tester artifact handoff guide only",
        FirstTesterProtocolMode.FIRST_TESTER_REVIEW_ONLY:
            "generate the first-tester post-test review template only",
        FirstTesterProtocolMode.REPORT_ONLY:
            "rebuild first-tester protocol reports from existing docs only",
        FirstTesterProtocolMode.DOCTOR_ONLY:
            "validate first-tester protocol prerequisites only",
    }
    if mode in purposes:
        p.purpose = purposes[mode]
    return p


def get_protocol_profile(profile_id: Optional[str] = None,
                         ) -> FirstTesterProtocolProfile:
    """Return the named profile, defaulting to ``first_tester_protocol_v0``."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_protocol_profile()
    for mode in FirstTesterProtocolMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_protocol_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default first-tester protocol profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0"
                                   for m in FirstTesterProtocolMode.ALL]
