"""Tester live-read-only profile -- the safe bridge from fixtures to live testing.

:class:`TesterLiveReadOnlyProfile` describes a bounded, local, live-read-only tester
run. The default profile (``tester_live_readonly_v0``) requires approved governance and
a feeder registry, requires tester confirmation, requires the environmental membrane
and Live Birth before downstream modules, blocks raw live-event fallback in strict
mode, and permits only external (operator-run) feeders -- Solaris never starts, stops,
schedules, or edits feeders, and never accesses network/shell/browser/OS/Git/GitHub or
controls hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class TesterLiveMode:
    TESTER_LIVE_READONLY = "tester_live_readonly"
    TESTER_LIVE_INIT_ONLY = "tester_live_init_only"
    TESTER_LIVE_DOCTOR_ONLY = "tester_live_doctor_only"
    TESTER_LIVE_BIRTH_ONLY = "tester_live_birth_only"
    TESTER_LIVE_MEMBRANE_ONLY = "tester_live_membrane_only"
    TESTER_LIVE_OBSERVATION_ONLY = "tester_live_observation_only"
    TESTER_LIVE_BUNDLE_ONLY = "tester_live_bundle_only"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (TESTER_LIVE_READONLY, TESTER_LIVE_INIT_ONLY, TESTER_LIVE_DOCTOR_ONLY,
           TESTER_LIVE_BIRTH_ONLY, TESTER_LIVE_MEMBRANE_ONLY,
           TESTER_LIVE_OBSERVATION_ONLY, TESTER_LIVE_BUNDLE_ONLY,
           REPORT_ONLY, DOCTOR_ONLY)


class TesterLiveConstraint:
    LIVE_READ_ONLY = "live_read_only"
    GOVERNANCE_REQUIRED = "governance_required"
    FEEDER_REGISTRY_REQUIRED = "feeder_registry_required"
    TESTER_CONFIRMATION_REQUIRED = "tester_confirmation_required"
    EXTERNAL_FEEDERS_ONLY = "external_feeders_only"
    NO_FEEDER_START = "solaris_may_not_start_feeders"
    NO_FEEDER_STOP = "solaris_may_not_stop_feeders"
    NO_FEEDER_EDIT = "solaris_may_not_edit_feeder_configs"
    NO_NETWORK_SHELL_GIT = "solaris_may_not_access_network_shell_os_git_github"
    NO_HARDWARE_CONTROL = "solaris_may_not_control_hardware"
    MEMBRANE_REQUIRED = "environmental_membrane_required"
    IMPRESSIONS_BEFORE_DOWNSTREAM = "sensory_impressions_required_before_downstream"
    BIRTH_BEFORE_OBSERVATION = "live_birth_required_before_observation"
    RAW_FALLBACK_BLOCKED_STRICT = "raw_live_event_fallback_blocked_in_strict_mode"
    BOUNDED_RUNTIME = "bounded_runtime"
    QUARANTINE_REQUIRED = "quarantine_required"
    CLAIMGUARD_IF_AVAILABLE = "claimguard_or_equivalent_scan_if_available"
    NO_UNSUPPORTED_CLAIMS = "no_unsupported_claims"

    ALL = (LIVE_READ_ONLY, GOVERNANCE_REQUIRED, FEEDER_REGISTRY_REQUIRED,
           TESTER_CONFIRMATION_REQUIRED, EXTERNAL_FEEDERS_ONLY, NO_FEEDER_START,
           NO_FEEDER_STOP, NO_FEEDER_EDIT, NO_NETWORK_SHELL_GIT,
           NO_HARDWARE_CONTROL, MEMBRANE_REQUIRED, IMPRESSIONS_BEFORE_DOWNSTREAM,
           BIRTH_BEFORE_OBSERVATION, RAW_FALLBACK_BLOCKED_STRICT,
           BOUNDED_RUNTIME, QUARANTINE_REQUIRED, CLAIMGUARD_IF_AVAILABLE,
           NO_UNSUPPORTED_CLAIMS)


DEFAULT_PROFILE_ID = "tester_live_readonly_v0"


@dataclass
class TesterLiveReadOnlyProfile:
    """A bounded, local, live-read-only tester profile (external feeders only)."""

    profile_id: str
    purpose: str
    mode: str = TesterLiveMode.TESTER_LIVE_READONLY
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 120.0
    max_events: int = 500
    governance_required: bool = True
    feeder_registry_required: bool = True
    tester_confirmation_required: bool = True
    require_membrane: bool = True
    require_birth_before_observation: bool = True
    external_feeders_only: bool = True
    run_birth: bool = True
    run_membrane: bool = True
    run_integration: bool = True
    run_observation: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in TesterLiveMode.ALL:
            self.mode = TesterLiveMode.TESTER_LIVE_READONLY
        # Per-mode stage gating (modes never silently skip; they scope the run).
        m = self.mode
        if m in (TesterLiveMode.TESTER_LIVE_INIT_ONLY,
                 TesterLiveMode.TESTER_LIVE_DOCTOR_ONLY,
                 TesterLiveMode.TESTER_LIVE_BUNDLE_ONLY,
                 TesterLiveMode.REPORT_ONLY, TesterLiveMode.DOCTOR_ONLY):
            self.run_birth = self.run_membrane = False
            self.run_integration = self.run_observation = False
        elif m == TesterLiveMode.TESTER_LIVE_BIRTH_ONLY:
            self.run_membrane = self.run_integration = False
            self.run_observation = False
        elif m == TesterLiveMode.TESTER_LIVE_MEMBRANE_ONLY:
            self.run_observation = False
        elif m == TesterLiveMode.TESTER_LIVE_OBSERVATION_ONLY:
            pass  # full pipeline through observation

    @property
    def is_init_only(self) -> bool:
        return self.mode == TesterLiveMode.TESTER_LIVE_INIT_ONLY

    @property
    def is_doctor_only(self) -> bool:
        return self.mode in (TesterLiveMode.TESTER_LIVE_DOCTOR_ONLY,
                             TesterLiveMode.DOCTOR_ONLY)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s, "max_events": self.max_events,
            "governance_required": self.governance_required,
            "feeder_registry_required": self.feeder_registry_required,
            "tester_confirmation_required": self.tester_confirmation_required,
            "require_membrane": self.require_membrane,
            "require_birth_before_observation":
                self.require_birth_before_observation,
            "external_feeders_only": self.external_feeders_only,
            "run_birth": self.run_birth, "run_membrane": self.run_membrane,
            "run_integration": self.run_integration,
            "run_observation": self.run_observation,
            "live_read_only": True, "solaris_starts_feeders": False,
            "limitations": list(self.limitations),
        }


def default_live_tester_profile() -> TesterLiveReadOnlyProfile:
    """The default tester live-read-only profile (external feeders only)."""
    return TesterLiveReadOnlyProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("a bounded, local, live-read-only tester run: prepare "
                 "governance + feeder registry templates and safe event packs, "
                 "then optionally run Live Birth -> Environmental Membrane -> "
                 "Membrane Integration -> Live Observation over the local inbox "
                 "while Solaris never starts/stops/schedules/controls feeders, "
                 "controls hardware, or accesses network/shell/Git/GitHub"),
        mode=TesterLiveMode.TESTER_LIVE_READONLY,
        constraints=list(TesterLiveConstraint.ALL),
        max_runtime_s=120.0, max_events=500,
        limitations=[
            "live-read-only; external feeders are manual/operator-run and "
            "Solaris never starts, stops, schedules, or edits them",
            "approved governance and a feeder registry are required before any "
            "live run",
            "the environmental membrane is required; downstream modules consume "
            "sensory impressions, never raw events",
            "Live Birth is required before observation; raw live-event fallback "
            "is blocked in strict mode",
            "the tester bundle is local-only; nothing is published or uploaded "
            "and tester feedback is never used as training",
            "live-read-only success is operational evidence, not evidence of "
            "consciousness/life/agency"])


def _profile_for_mode(mode: str) -> TesterLiveReadOnlyProfile:
    p = default_live_tester_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    p.__post_init__()
    purposes = {
        TesterLiveMode.TESTER_LIVE_INIT_ONLY:
            "write tester live templates + state layout only (no live run)",
        TesterLiveMode.TESTER_LIVE_DOCTOR_ONLY:
            "run the live tester doctor only",
        TesterLiveMode.TESTER_LIVE_BIRTH_ONLY:
            "run Live Birth over the local inbox only",
        TesterLiveMode.TESTER_LIVE_MEMBRANE_ONLY:
            "run Live Birth + Environmental Membrane (+ integration) only",
        TesterLiveMode.TESTER_LIVE_OBSERVATION_ONLY:
            "run the full live-read-only pipeline through observation",
        TesterLiveMode.TESTER_LIVE_BUNDLE_ONLY:
            "build the local tester live bundle from existing state only",
        TesterLiveMode.REPORT_ONLY:
            "rebuild tester live reports from existing state only",
        TesterLiveMode.DOCTOR_ONLY:
            "validate tester live prerequisites only",
    }
    if mode in purposes:
        p.purpose = purposes[mode]
    return p


def get_live_tester_profile(profile_id: Optional[str] = None,
                            ) -> TesterLiveReadOnlyProfile:
    """Return the named profile, defaulting to ``tester_live_readonly_v0``."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_live_tester_profile()
    for mode in TesterLiveMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_live_tester_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default tester live-read-only profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in TesterLiveMode.ALL]
