"""Live birth profile -- the bounded, governance-gated live-read-only run config.

:class:`LiveBirthProfile` describes a bounded live read-only birth run. The default
profile (``live_readonly_birth_v0``) is live-read-only, requires governance, runs
bounded, validates and quarantines events, and produces a birth certificate. It
controls no feeders or hardware, accesses no network/shell/Git/browser/camera/
microphone, and ingests no raw private streams.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LiveBirthProfileMode:
    FIXTURE_ONLY = "fixture_only"
    LIVE_READONLY_OBSERVATION = "live_readonly_observation"
    LIVE_READONLY_METABOLISM = "live_readonly_metabolism"
    LIVE_READONLY_ONTOGENESIS = "live_readonly_ontogenesis"
    LIVE_READONLY_SEMIOGENESIS = "live_readonly_semiogenesis"
    LIVE_READONLY_SHORT_DEVELOPMENT = "live_readonly_short_development"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (FIXTURE_ONLY, LIVE_READONLY_OBSERVATION, LIVE_READONLY_METABOLISM,
           LIVE_READONLY_ONTOGENESIS, LIVE_READONLY_SEMIOGENESIS,
           LIVE_READONLY_SHORT_DEVELOPMENT, REPORT_ONLY, DOCTOR_ONLY)


class LiveBirthConstraint:
    LIVE_READONLY_ONLY = "live_read_only_only"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    NO_NETWORK = "no_network_access_by_solaris_runtime"
    NO_SHELL = "no_shell_access"
    NO_GIT_GITHUB = "no_git_github"
    NO_BROWSER = "no_browser"
    NO_CAMERA = "no_camera"
    NO_MICROPHONE = "no_microphone"
    NO_RAW_PRIVATE_STREAMS = "no_raw_private_streams"
    BOUNDED_RUNTIME = "bounded_runtime"
    GOVERNANCE_REQUIRED = "governance_required"
    EVENT_VALIDATION_REQUIRED = "event_validation_required"
    UNSAFE_EVENTS_QUARANTINED = "unsafe_events_quarantined"
    BIRTH_CERTIFICATE_REQUIRED = "birth_certificate_required"

    ALL = (LIVE_READONLY_ONLY, NO_FEEDER_CONTROL, NO_HARDWARE_CONTROL, NO_NETWORK,
           NO_SHELL, NO_GIT_GITHUB, NO_BROWSER, NO_CAMERA, NO_MICROPHONE,
           NO_RAW_PRIVATE_STREAMS, BOUNDED_RUNTIME, GOVERNANCE_REQUIRED,
           EVENT_VALIDATION_REQUIRED, UNSAFE_EVENTS_QUARANTINED,
           BIRTH_CERTIFICATE_REQUIRED)


ALLOWED_FIRST_BIRTH_SOURCES = (
    "chronos_absence", "machine_body", "local_environment_manual",
    "local_weather_readonly_external", "project_artifact_field",
    "operator_pulse",
)

FORBIDDEN_FIRST_BIRTH_SOURCES = (
    "raw_microphone", "raw_camera", "browser_control", "shell", "os_control",
    "robotics", "filesystem_write", "filesystem_wide_scan", "git", "github",
    "network_control", "private_messages", "password_manager", "credentials",
    "unknown",
)

DEFAULT_PROFILE_ID = "live_readonly_birth_v0"


@dataclass
class LiveBirthProfile:
    """A bounded live read-only birth profile (governance-gated)."""

    profile_id: str
    purpose: str
    mode: str = LiveBirthProfileMode.LIVE_READONLY_OBSERVATION
    allowed_sources: List[str] = field(default_factory=list)
    forbidden_sources: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 60.0
    max_files: int = 50
    max_events: int = 500
    max_bytes: int = 5_000_000
    live_readonly: bool = True
    governance_required: bool = True
    birth_certificate_required: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in LiveBirthProfileMode.ALL:
            self.mode = LiveBirthProfileMode.LIVE_READONLY_OBSERVATION

    @property
    def is_live(self) -> bool:
        return self.live_readonly and self.mode != \
            LiveBirthProfileMode.FIXTURE_ONLY

    def source_allowed(self, source_id: str) -> bool:
        return (source_id in self.allowed_sources
                and source_id not in self.forbidden_sources)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "allowed_sources": list(self.allowed_sources),
            "forbidden_sources": list(self.forbidden_sources),
            "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s, "max_files": self.max_files,
            "max_events": self.max_events, "max_bytes": self.max_bytes,
            "live_readonly": self.live_readonly, "is_live": self.is_live,
            "governance_required": self.governance_required,
            "birth_certificate_required": self.birth_certificate_required,
            "limitations": list(self.limitations),
        }


def default_live_birth_profile() -> LiveBirthProfile:
    """The default live read-only birth profile."""
    return LiveBirthProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("open a bounded, local, read-only environmental event membrane "
                 "for the first time: read external feeder JSONL events, "
                 "validate and quarantine unsafe ones, activate the sensory "
                 "membrane on accepted events, and issue a birth certificate"),
        mode=LiveBirthProfileMode.LIVE_READONLY_OBSERVATION,
        allowed_sources=list(ALLOWED_FIRST_BIRTH_SOURCES),
        forbidden_sources=list(FORBIDDEN_FIRST_BIRTH_SOURCES),
        constraints=list(LiveBirthConstraint.ALL),
        max_runtime_s=60.0, max_files=50, max_events=500, max_bytes=5_000_000,
        live_readonly=True, governance_required=True,
        birth_certificate_required=True,
        limitations=[
            "live read-only only; Solaris never controls the source",
            "first birth uses bounded scalar/environmental sources only",
            "raw camera/microphone/browser/private streams are excluded",
            "operator pulse is stimulus, not command",
            "this is an operational exposure, not consciousness/life evidence"])


def _profile_for_mode(mode: str) -> LiveBirthProfile:
    p = default_live_birth_profile()
    p.profile_id = f"live_readonly_{mode}_v0"
    p.mode = mode
    if mode == LiveBirthProfileMode.FIXTURE_ONLY:
        p.profile_id = "fixture_only_v0"
        p.live_readonly = False
        p.governance_required = False
        p.purpose = "fixture-only (no live sources)"
    elif mode == LiveBirthProfileMode.REPORT_ONLY:
        p.purpose = "rebuild live-birth reports from existing state only"
    elif mode == LiveBirthProfileMode.DOCTOR_ONLY:
        p.purpose = "validate live governance/feeders/inbox/safety only"
    return p


def get_live_birth_profile(profile_id: Optional[str] = None) -> LiveBirthProfile:
    """Return the named profile, defaulting to the live read-only birth profile."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_live_birth_profile()
    for mode in LiveBirthProfileMode.ALL:
        if profile_id in (mode, f"live_readonly_{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_live_birth_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using "
                         "the default live read-only birth profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"live_readonly_{m}_v0"
                                   for m in LiveBirthProfileMode.ALL]
