"""Environmental membrane profile -- bounded, read-only perceptual-boundary config.

:class:`EnvironmentalMembraneProfile` describes a bounded membrane run. The default
profile (``environmental_membrane_v0``) is live-read-only: it requires governance and
a feeder registry for live modes, requires event validation, accepts only validated
events, preserves quarantine, requires sensory impressions before any downstream
learning, attenuates the operator pulse, and never treats human labels or debug
gloss as ground truth. It controls no feeders and no hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class MembraneProfileMode:
    FIXTURE_MEMBRANE = "fixture_membrane"
    LIVE_MEMBRANE_OBSERVATION = "live_membrane_observation"
    LIVE_MEMBRANE_BIRTH = "live_membrane_birth"
    LIVE_MEMBRANE_METABOLISM = "live_membrane_metabolism"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (FIXTURE_MEMBRANE, LIVE_MEMBRANE_OBSERVATION, LIVE_MEMBRANE_BIRTH,
           LIVE_MEMBRANE_METABOLISM, REPORT_ONLY, DOCTOR_ONLY)

    LIVE = (LIVE_MEMBRANE_OBSERVATION, LIVE_MEMBRANE_BIRTH,
            LIVE_MEMBRANE_METABOLISM)


class MembraneConstraint:
    LIVE_READONLY_ONLY = "live_read_only_only"
    GOVERNANCE_REQUIRED_LIVE = "governance_required_for_live_mode"
    FEEDER_REGISTRY_REQUIRED_LIVE = "feeder_registry_required_for_live_mode"
    EVENT_VALIDATION_REQUIRED = "event_validation_required"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    NO_NETWORK_SHELL_GIT = "no_network_shell_browser_os_git_github"
    BOUNDED_RUNTIME = "bounded_runtime"
    ACCEPTED_EVENTS_ONLY = "accepted_events_only"
    QUARANTINE_PRESERVED = "quarantine_preserved"
    IMPRESSIONS_BEFORE_LEARNING = "sensory_impressions_required_before_learning"
    OPERATOR_PULSE_WEIGHT_LIMITED = "operator_pulse_weight_limited"
    HUMAN_LABELS_NOT_GROUND_TRUTH = "human_labels_not_ground_truth"
    DEBUG_GLOSS_NOT_GROUND_TRUTH = "debug_gloss_not_ground_truth"
    SOURCE_PRESSURE_TRACKED = "source_pressure_tracked"
    CONTAMINATION_TRACKED = "contamination_tracked"
    SOURCE_DOMINANCE_TRACKED = "source_dominance_tracked"
    UNSAFE_IMPRESSIONS_BLOCKED = "unsafe_impressions_blocked"

    ALL = (LIVE_READONLY_ONLY, GOVERNANCE_REQUIRED_LIVE,
           FEEDER_REGISTRY_REQUIRED_LIVE, EVENT_VALIDATION_REQUIRED,
           NO_FEEDER_CONTROL, NO_HARDWARE_CONTROL, NO_NETWORK_SHELL_GIT,
           BOUNDED_RUNTIME, ACCEPTED_EVENTS_ONLY, QUARANTINE_PRESERVED,
           IMPRESSIONS_BEFORE_LEARNING, OPERATOR_PULSE_WEIGHT_LIMITED,
           HUMAN_LABELS_NOT_GROUND_TRUTH, DEBUG_GLOSS_NOT_GROUND_TRUTH,
           SOURCE_PRESSURE_TRACKED, CONTAMINATION_TRACKED,
           SOURCE_DOMINANCE_TRACKED, UNSAFE_IMPRESSIONS_BLOCKED)


DEFAULT_PROFILE_ID = "environmental_membrane_v0"


@dataclass
class EnvironmentalMembraneProfile:
    """A bounded environmental-membrane profile (read-only perceptual boundary)."""

    profile_id: str
    purpose: str
    mode: str = MembraneProfileMode.LIVE_MEMBRANE_OBSERVATION
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 120.0
    max_events: int = 2000
    max_files: int = 100
    operator_pulse_salience_cap: float = 0.4
    human_text_salience_cap: float = 0.5
    governance_required: bool = True
    feeder_registry_required: bool = True
    event_validation_required: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in MembraneProfileMode.ALL:
            self.mode = MembraneProfileMode.LIVE_MEMBRANE_OBSERVATION
        if self.mode == MembraneProfileMode.FIXTURE_MEMBRANE:
            self.governance_required = False
            self.feeder_registry_required = False

    @property
    def is_live(self) -> bool:
        return self.mode in MembraneProfileMode.LIVE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "is_live": self.is_live,
            "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s, "max_events": self.max_events,
            "max_files": self.max_files,
            "operator_pulse_salience_cap": self.operator_pulse_salience_cap,
            "human_text_salience_cap": self.human_text_salience_cap,
            "governance_required": self.governance_required,
            "feeder_registry_required": self.feeder_registry_required,
            "event_validation_required": self.event_validation_required,
            "limitations": list(self.limitations),
        }


def default_membrane_profile() -> EnvironmentalMembraneProfile:
    """The default environmental-membrane profile (live observation, read-only)."""
    return EnvironmentalMembraneProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("convert validated live read-only events into sensory "
                 "impressions through receptor matching, permeability "
                 "regulation, salience modulation, source-pressure analysis, "
                 "contamination checks, immune responses, and membrane memory -- "
                 "the perceptual boundary between external events and Solaris "
                 "perception"),
        mode=MembraneProfileMode.LIVE_MEMBRANE_OBSERVATION,
        constraints=list(MembraneConstraint.ALL),
        max_runtime_s=120.0, max_events=2000, max_files=100,
        operator_pulse_salience_cap=0.4, human_text_salience_cap=0.5,
        governance_required=True, feeder_registry_required=True,
        event_validation_required=True,
        limitations=[
            "live read-only only; the membrane controls no feeders or hardware",
            "validated events are not yet perception; sensory impressions are",
            "operator pulse is attenuated stimulus, not teaching; labels/gloss "
            "are not ground truth",
            "downstream modules must consume sensory impressions, not raw "
            "events, once the membrane is integrated",
            "sensory impressions are operational boundary records, not evidence "
            "of consciousness/life/agency"])


def _profile_for_mode(mode: str) -> EnvironmentalMembraneProfile:
    p = default_membrane_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    p.__post_init__()
    if mode == MembraneProfileMode.FIXTURE_MEMBRANE:
        p.purpose = "fixture-only membrane (no governance/feeder requirement)"
    elif mode == MembraneProfileMode.LIVE_MEMBRANE_BIRTH:
        p.purpose = "membrane activation during live read-only birth"
    elif mode == MembraneProfileMode.LIVE_MEMBRANE_METABOLISM:
        p.purpose = "membrane feeding perceptual metabolism (report-only handoff)"
    elif mode == MembraneProfileMode.REPORT_ONLY:
        p.purpose = "rebuild membrane reports from existing state only"
    elif mode == MembraneProfileMode.DOCTOR_ONLY:
        p.purpose = "validate membrane prerequisites only"
    return p


def get_membrane_profile(profile_id: Optional[str] = None,
                         ) -> EnvironmentalMembraneProfile:
    """Return the named profile, defaulting to the live-observation membrane."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_membrane_profile()
    for mode in MembraneProfileMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_membrane_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default environmental-membrane profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in MembraneProfileMode.ALL]
