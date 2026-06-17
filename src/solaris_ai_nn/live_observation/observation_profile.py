"""Live observation profile -- bounded, read-only, no-learning configuration.

:class:`LiveObservationProfile` describes a bounded post-birth observation run. The
default profile (``post_birth_observation_v0``) is live-read-only with no concept
birth, no sign birth, and no developmental learning; it requires governance and a
birth certificate (unless explicitly waived for a demo), accepts only validated
events, preserves quarantine, and treats operator pulses as stimulus only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LiveObservationMode:
    POST_BIRTH_OBSERVATION_2H = "post_birth_observation_2h"
    POST_BIRTH_OBSERVATION_6H = "post_birth_observation_6h"
    FIRST_DAY_METABOLISM_24H = "first_day_metabolism_24h"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (POST_BIRTH_OBSERVATION_2H, POST_BIRTH_OBSERVATION_6H,
           FIRST_DAY_METABOLISM_24H, REPORT_ONLY, DOCTOR_ONLY)


class LiveObservationConstraint:
    LIVE_READONLY_ONLY = "live_read_only_only"
    NO_CONCEPT_BIRTH = "no_concept_birth"
    NO_SIGN_BIRTH = "no_sign_birth"
    NO_DEVELOPMENTAL_LEARNING = "no_developmental_learning_by_default"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    NO_NETWORK_SHELL_GIT = "no_network_shell_browser_os_git_github"
    BOUNDED_RUNTIME = "bounded_runtime"
    GOVERNANCE_REQUIRED = "governance_required"
    BIRTH_CERTIFICATE_REQUIRED = "birth_certificate_required"
    ACCEPTED_EVENTS_ONLY = "accepted_events_only"
    QUARANTINE_PRESERVED = "quarantine_preserved"
    OPERATOR_PULSE_STIMULUS_ONLY = "operator_pulse_is_stimulus_only"
    HUMAN_LABELS_NOT_GROUND_TRUTH = "human_labels_not_ground_truth"
    DEBUG_GLOSS_NOT_GROUND_TRUTH = "debug_gloss_not_ground_truth"

    ALL = (LIVE_READONLY_ONLY, NO_CONCEPT_BIRTH, NO_SIGN_BIRTH,
           NO_DEVELOPMENTAL_LEARNING, NO_FEEDER_CONTROL, NO_HARDWARE_CONTROL,
           NO_NETWORK_SHELL_GIT, BOUNDED_RUNTIME, GOVERNANCE_REQUIRED,
           BIRTH_CERTIFICATE_REQUIRED, ACCEPTED_EVENTS_ONLY,
           QUARANTINE_PRESERVED, OPERATOR_PULSE_STIMULUS_ONLY,
           HUMAN_LABELS_NOT_GROUND_TRUTH, DEBUG_GLOSS_NOT_GROUND_TRUTH)


DEFAULT_PROFILE_ID = "post_birth_observation_v0"


@dataclass
class LiveObservationProfile:
    """A bounded post-birth observation profile (no learning by default)."""

    profile_id: str
    purpose: str
    mode: str = LiveObservationMode.POST_BIRTH_OBSERVATION_2H
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 120.0
    max_events: int = 2000
    max_files: int = 100
    observation_window_minutes: int = 30
    learning_enabled: bool = False
    governance_required: bool = True
    birth_certificate_required: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in LiveObservationMode.ALL:
            self.mode = LiveObservationMode.POST_BIRTH_OBSERVATION_2H

    @property
    def is_metabolism_phase(self) -> bool:
        return self.mode == LiveObservationMode.FIRST_DAY_METABOLISM_24H

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s, "max_events": self.max_events,
            "max_files": self.max_files,
            "observation_window_minutes": self.observation_window_minutes,
            "learning_enabled": self.learning_enabled,
            "is_metabolism_phase": self.is_metabolism_phase,
            "governance_required": self.governance_required,
            "birth_certificate_required": self.birth_certificate_required,
            "limitations": list(self.limitations),
        }


def default_observation_profile() -> LiveObservationProfile:
    """The default post-birth observation profile (2h, no learning)."""
    return LiveObservationProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("observe a bounded live read-only event stream after birth, "
                 "without learning: measure source health, source diet, rhythm, "
                 "absence, overload/deprivation, and report-only metabolism "
                 "calibration, and decide via a stability gate whether later "
                 "phases are safe"),
        mode=LiveObservationMode.POST_BIRTH_OBSERVATION_2H,
        constraints=list(LiveObservationConstraint.ALL),
        max_runtime_s=120.0, max_events=2000, max_files=100,
        observation_window_minutes=30,
        learning_enabled=False, governance_required=True,
        birth_certificate_required=True,
        limitations=[
            "live read-only only; no learning is enabled",
            "no concept birth, no sign birth, no developmental learning",
            "operator pulse is stimulus, not command; labels/gloss are not "
            "ground truth",
            "metabolism calibration is report-only; nothing is updated",
            "this is observational stabilization, not consciousness/life "
            "evidence"])


def _profile_for_mode(mode: str) -> LiveObservationProfile:
    p = default_observation_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    if mode == LiveObservationMode.POST_BIRTH_OBSERVATION_6H:
        p.purpose = "6-hour post-birth observation (no learning)"
    elif mode == LiveObservationMode.FIRST_DAY_METABOLISM_24H:
        p.purpose = "24-hour first-day perceptual metabolism calibration phase"
        p.observation_window_minutes = 60
    elif mode == LiveObservationMode.REPORT_ONLY:
        p.purpose = "rebuild observation reports from existing state only"
    elif mode == LiveObservationMode.DOCTOR_ONLY:
        p.purpose = "validate observation prerequisites only"
    return p


def get_observation_profile(profile_id: Optional[str] = None,
                            ) -> LiveObservationProfile:
    """Return the named profile, defaulting to the post-birth observation one."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_observation_profile()
    for mode in LiveObservationMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_observation_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default post-birth observation profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in LiveObservationMode.ALL]
