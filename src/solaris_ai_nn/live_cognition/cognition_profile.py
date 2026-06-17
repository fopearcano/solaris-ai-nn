"""Live cognition profile -- bounded, read-only, conservative, trace-first.

:class:`LiveCognitionProfile` describes a bounded first live cognition run. The
default profile (``live_cognition_trace_v0``) forms cognition *traces* only -- it does
not enable real-world action, action-reaction learning, developmental autonomy, or
self-boundary tracking. It requires governance, a birth certificate, an unblocked
observation stability gate, live concept memory, and live sign memory; private signs
are not language; anticipation requires evidence; prediction assessment is required;
and contaminated traces cannot be promoted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LiveCognitionMode:
    TRACE_ONLY = "live_cognition_trace_only"
    ANTICIPATION_LIMITED = "live_cognition_anticipation_limited"
    INTERNAL_SIMULATION_LIMITED = "live_cognition_internal_simulation_limited"
    COGNITION_7D = "live_cognition_7d"
    COGNITION_14D = "live_cognition_14d"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (TRACE_ONLY, ANTICIPATION_LIMITED, INTERNAL_SIMULATION_LIMITED,
           COGNITION_7D, COGNITION_14D, REPORT_ONLY, DOCTOR_ONLY)


class LiveCognitionConstraint:
    LIVE_READONLY_ONLY = "live_read_only_only"
    GOVERNANCE_REQUIRED = "governance_required"
    BIRTH_CERTIFICATE_REQUIRED = "birth_certificate_required"
    OBSERVATION_STABILITY_REQUIRED = "observation_stability_gate_required"
    CONCEPT_MEMORY_REQUIRED = "live_concept_memory_required"
    SIGN_MEMORY_REQUIRED = "live_sign_memory_required"
    SIGN_BIRTH_GATE_REQUIRED = "sign_birth_gate_required"
    NO_EXTERNAL_ACTION = "no_external_action"
    NO_ACTION_REACTION = "no_action_reaction_learning_by_default"
    NO_DEVELOPMENTAL_AUTONOMY = "no_developmental_autonomy_by_default"
    NO_SELF_BOUNDARY = "no_self_boundary_tracking_by_default"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    NO_NETWORK_SHELL_GIT = "no_network_shell_browser_os_git_github"
    BOUNDED_RUNTIME = "bounded_runtime"
    ACCEPTED_EVIDENCE_ONLY = "accepted_evidence_only"
    QUARANTINE_PRESERVED = "quarantine_preserved"
    OPERATOR_PULSE_WEIGHT_LIMITED = "operator_pulse_weight_limited"
    HUMAN_LABELS_NOT_GROUND_TRUTH = "human_labels_not_ground_truth"
    DEBUG_GLOSS_NOT_GROUND_TRUTH = "debug_gloss_not_ground_truth"
    SIGNS_NOT_LANGUAGE = "private_signs_are_not_language"
    ANTICIPATION_EVIDENCE_REQUIRED = "anticipation_evidence_required"
    PREDICTION_ASSESSMENT_REQUIRED = "prediction_assessment_required"
    CONTAMINATED_TRACES_BLOCKED = "contaminated_cognition_traces_cannot_promote"

    ALL = (LIVE_READONLY_ONLY, GOVERNANCE_REQUIRED, BIRTH_CERTIFICATE_REQUIRED,
           OBSERVATION_STABILITY_REQUIRED, CONCEPT_MEMORY_REQUIRED,
           SIGN_MEMORY_REQUIRED, SIGN_BIRTH_GATE_REQUIRED, NO_EXTERNAL_ACTION,
           NO_ACTION_REACTION, NO_DEVELOPMENTAL_AUTONOMY, NO_SELF_BOUNDARY,
           NO_FEEDER_CONTROL, NO_HARDWARE_CONTROL, NO_NETWORK_SHELL_GIT,
           BOUNDED_RUNTIME, ACCEPTED_EVIDENCE_ONLY, QUARANTINE_PRESERVED,
           OPERATOR_PULSE_WEIGHT_LIMITED, HUMAN_LABELS_NOT_GROUND_TRUTH,
           DEBUG_GLOSS_NOT_GROUND_TRUTH, SIGNS_NOT_LANGUAGE,
           ANTICIPATION_EVIDENCE_REQUIRED, PREDICTION_ASSESSMENT_REQUIRED,
           CONTAMINATED_TRACES_BLOCKED)


DEFAULT_PROFILE_ID = "live_cognition_trace_v0"


@dataclass
class LiveCognitionProfile:
    """A bounded first live cognition profile (trace-first, no action)."""

    profile_id: str
    purpose: str
    mode: str = LiveCognitionMode.TRACE_ONLY
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 180.0
    max_signs: int = 200
    max_traces: int = 200
    max_simulation_steps: int = 8
    max_traversal_depth: int = 3
    min_prediction_utility: float = 0.5
    max_uncertainty: float = 0.6
    allow_anticipation: bool = False
    allow_internal_simulation: bool = False
    action_enabled: bool = False
    action_reaction_enabled: bool = False
    developmental_autonomy_enabled: bool = False
    self_boundary_enabled: bool = False
    governance_required: bool = True
    birth_certificate_required: bool = True
    observation_stability_required: bool = True
    concept_memory_required: bool = True
    sign_memory_required: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in LiveCognitionMode.ALL:
            self.mode = LiveCognitionMode.TRACE_ONLY
        if self.mode in (LiveCognitionMode.ANTICIPATION_LIMITED,
                         LiveCognitionMode.COGNITION_7D,
                         LiveCognitionMode.COGNITION_14D):
            self.allow_anticipation = True
        if self.mode in (LiveCognitionMode.INTERNAL_SIMULATION_LIMITED,
                         LiveCognitionMode.COGNITION_7D,
                         LiveCognitionMode.COGNITION_14D):
            self.allow_anticipation = True
            self.allow_internal_simulation = True

    @property
    def trace_only(self) -> bool:
        return not self.allow_anticipation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s, "max_signs": self.max_signs,
            "max_traces": self.max_traces,
            "max_simulation_steps": self.max_simulation_steps,
            "max_traversal_depth": self.max_traversal_depth,
            "min_prediction_utility": self.min_prediction_utility,
            "max_uncertainty": self.max_uncertainty,
            "allow_anticipation": self.allow_anticipation,
            "allow_internal_simulation": self.allow_internal_simulation,
            "trace_only": self.trace_only,
            "action_enabled": self.action_enabled,
            "action_reaction_enabled": self.action_reaction_enabled,
            "developmental_autonomy_enabled":
                self.developmental_autonomy_enabled,
            "self_boundary_enabled": self.self_boundary_enabled,
            "governance_required": self.governance_required,
            "birth_certificate_required": self.birth_certificate_required,
            "observation_stability_required":
                self.observation_stability_required,
            "concept_memory_required": self.concept_memory_required,
            "sign_memory_required": self.sign_memory_required,
            "limitations": list(self.limitations),
        }


def default_cognition_profile() -> LiveCognitionProfile:
    """The default first-live-cognition profile (trace-only, no action)."""
    return LiveCognitionProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("form bounded sign-based anticipation and relation traces over "
                 "stable live private signs and feature-grounded proto-concepts: "
                 "build cognition traces, generate anticipations, estimate "
                 "uncertainty, traverse private relations, run bounded internal "
                 "simulations, and assess predictions -- without real-world "
                 "action, action-reaction learning, developmental autonomy, or "
                 "self-boundary tracking"),
        mode=LiveCognitionMode.TRACE_ONLY,
        constraints=list(LiveCognitionConstraint.ALL),
        max_runtime_s=180.0, max_signs=200, max_traces=200,
        max_simulation_steps=8, max_traversal_depth=3,
        min_prediction_utility=0.5, max_uncertainty=0.6,
        allow_anticipation=False, allow_internal_simulation=False,
        action_enabled=False, action_reaction_enabled=False,
        developmental_autonomy_enabled=False, self_boundary_enabled=False,
        governance_required=True, birth_certificate_required=True,
        observation_stability_required=True, concept_memory_required=True,
        sign_memory_required=True,
        limitations=[
            "trace-first; anticipation and internal simulation are gated",
            "no real-world action, no action-reaction learning, no "
            "developmental autonomy, no self-boundary tracking by default",
            "private signs are not language; labels/gloss are not ground truth; "
            "operator pulse is stimulus, not teaching",
            "internal simulation is bounded offline metadata; it controls "
            "nothing and is compared against later observed events",
            "cognition traces are operational anticipation/relation records, "
            "not reasoning, understanding, consciousness, or agency"])


def _profile_for_mode(mode: str) -> LiveCognitionProfile:
    p = default_cognition_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    p.__post_init__()
    if mode == LiveCognitionMode.ANTICIPATION_LIMITED:
        p.purpose = "limited sign-based anticipation over stable signs"
    elif mode == LiveCognitionMode.INTERNAL_SIMULATION_LIMITED:
        p.purpose = "limited bounded internal simulation over stable signs"
    elif mode == LiveCognitionMode.COGNITION_7D:
        p.purpose = "7-day bounded live cognition (traces + anticipation + sim)"
    elif mode == LiveCognitionMode.COGNITION_14D:
        p.purpose = "14-day bounded live cognition (traces + anticipation + sim)"
    elif mode == LiveCognitionMode.REPORT_ONLY:
        p.purpose = "rebuild cognition reports from existing state only"
    elif mode == LiveCognitionMode.DOCTOR_ONLY:
        p.purpose = "validate cognition prerequisites only"
    return p


def get_cognition_profile(profile_id: Optional[str] = None,
                          ) -> LiveCognitionProfile:
    """Return the named profile, defaulting to the trace-only one."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_cognition_profile()
    for mode in LiveCognitionMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_cognition_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default trace-only cognition profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in LiveCognitionMode.ALL]
