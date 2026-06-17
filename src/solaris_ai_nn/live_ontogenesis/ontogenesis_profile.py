"""Live ontogenesis profile -- bounded, read-only, conservative, candidate-first.

:class:`LiveOntogenesisProfile` describes a bounded first live ontogenesis run. The
default profile (``live_ontogenesis_candidate_v0``) forms proto-concept *candidates*
only -- it does not enable semiogenesis, action-reaction learning, or developmental
autonomy. It requires governance, a birth certificate, and an unblocked observation
stability gate, accepts only validated events, preserves quarantine, limits the
operator-pulse weight, and never treats human labels or debug glosses as ground
truth. Concept birth requires feature evidence and is conservative.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LiveOntogenesisMode:
    CANDIDATE_ONLY = "live_ontogenesis_candidate_only"
    BIRTH_LIMITED = "live_ontogenesis_birth_limited"
    ONTOGENESIS_3D = "live_ontogenesis_3d"
    ONTOGENESIS_7D = "live_ontogenesis_7d"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (CANDIDATE_ONLY, BIRTH_LIMITED, ONTOGENESIS_3D, ONTOGENESIS_7D,
           REPORT_ONLY, DOCTOR_ONLY)


class LiveOntogenesisConstraint:
    LIVE_READONLY_ONLY = "live_read_only_only"
    GOVERNANCE_REQUIRED = "governance_required"
    BIRTH_CERTIFICATE_REQUIRED = "birth_certificate_required"
    OBSERVATION_STABILITY_REQUIRED = "observation_stability_gate_required"
    NO_SEMIOGENESIS = "no_semiogenesis_by_default"
    NO_ACTION_REACTION = "no_action_reaction_learning_by_default"
    NO_DEVELOPMENTAL_AUTONOMY = "no_developmental_autonomy_by_default"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    NO_NETWORK_SHELL_GIT = "no_network_shell_browser_os_git_github"
    BOUNDED_RUNTIME = "bounded_runtime"
    ACCEPTED_EVENTS_ONLY = "accepted_events_only"
    QUARANTINE_PRESERVED = "quarantine_preserved"
    OPERATOR_PULSE_WEIGHT_LIMITED = "operator_pulse_weight_limited"
    HUMAN_LABELS_NOT_GROUND_TRUTH = "human_labels_not_ground_truth"
    DEBUG_GLOSS_NOT_GROUND_TRUTH = "debug_gloss_not_ground_truth"
    FEATURE_EVIDENCE_REQUIRED = "feature_evidence_required_for_concept_birth"
    SOURCE_DIET_DOMINANCE_BLOCKS = "source_diet_dominance_blocks_or_weakens_birth"
    SEVERE_LOAD_BLOCKS = "severe_overload_or_deprivation_blocks_concept_birth"

    ALL = (LIVE_READONLY_ONLY, GOVERNANCE_REQUIRED, BIRTH_CERTIFICATE_REQUIRED,
           OBSERVATION_STABILITY_REQUIRED, NO_SEMIOGENESIS, NO_ACTION_REACTION,
           NO_DEVELOPMENTAL_AUTONOMY, NO_FEEDER_CONTROL, NO_HARDWARE_CONTROL,
           NO_NETWORK_SHELL_GIT, BOUNDED_RUNTIME, ACCEPTED_EVENTS_ONLY,
           QUARANTINE_PRESERVED, OPERATOR_PULSE_WEIGHT_LIMITED,
           HUMAN_LABELS_NOT_GROUND_TRUTH, DEBUG_GLOSS_NOT_GROUND_TRUTH,
           FEATURE_EVIDENCE_REQUIRED, SOURCE_DIET_DOMINANCE_BLOCKS,
           SEVERE_LOAD_BLOCKS)


DEFAULT_PROFILE_ID = "live_ontogenesis_candidate_v0"


@dataclass
class LiveOntogenesisProfile:
    """A bounded first live ontogenesis profile (candidate-first, no semiogenesis)."""

    profile_id: str
    purpose: str
    mode: str = LiveOntogenesisMode.CANDIDATE_ONLY
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 180.0
    max_events: int = 2000
    max_candidates: int = 200
    min_recurrence: int = 3
    min_stability: float = 0.6
    allow_limited_birth: bool = False
    semiogenesis_enabled: bool = False
    action_reaction_enabled: bool = False
    developmental_autonomy_enabled: bool = False
    governance_required: bool = True
    birth_certificate_required: bool = True
    observation_stability_required: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in LiveOntogenesisMode.ALL:
            self.mode = LiveOntogenesisMode.CANDIDATE_ONLY
        if self.mode in (LiveOntogenesisMode.BIRTH_LIMITED,
                         LiveOntogenesisMode.ONTOGENESIS_3D,
                         LiveOntogenesisMode.ONTOGENESIS_7D):
            self.allow_limited_birth = True

    @property
    def candidate_only(self) -> bool:
        return not self.allow_limited_birth

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s, "max_events": self.max_events,
            "max_candidates": self.max_candidates,
            "min_recurrence": self.min_recurrence,
            "min_stability": self.min_stability,
            "allow_limited_birth": self.allow_limited_birth,
            "candidate_only": self.candidate_only,
            "semiogenesis_enabled": self.semiogenesis_enabled,
            "action_reaction_enabled": self.action_reaction_enabled,
            "developmental_autonomy_enabled":
                self.developmental_autonomy_enabled,
            "governance_required": self.governance_required,
            "birth_certificate_required": self.birth_certificate_required,
            "observation_stability_required":
                self.observation_stability_required,
            "limitations": list(self.limitations),
        }


def default_ontogenesis_profile() -> LiveOntogenesisProfile:
    """The default first-live-ontogenesis profile (candidates only, no semiogenesis)."""
    return LiveOntogenesisProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("form conservative proto-concept candidates from validated "
                 "live read-only feature recurrence after birth and observation "
                 "stability: extract features, track recurrence, score "
                 "stability, filter contamination, and gate concept birth "
                 "conservatively -- without semiogenesis, action-reaction "
                 "learning, or developmental autonomy"),
        mode=LiveOntogenesisMode.CANDIDATE_ONLY,
        constraints=list(LiveOntogenesisConstraint.ALL),
        max_runtime_s=180.0, max_events=2000, max_candidates=200,
        min_recurrence=3, min_stability=0.6, allow_limited_birth=False,
        semiogenesis_enabled=False, action_reaction_enabled=False,
        developmental_autonomy_enabled=False,
        governance_required=True, birth_certificate_required=True,
        observation_stability_required=True,
        limitations=[
            "candidate-first; concept birth is conservative and gated",
            "no semiogenesis, no action-reaction learning, no developmental "
            "autonomy by default",
            "operator pulse is stimulus, not teaching; labels/gloss are not "
            "ground truth",
            "proto-concepts are operational feature-stability records, not "
            "understanding",
            "this is not consciousness/life evidence and proves nothing about "
            "consciousness/life/agency"])


def _profile_for_mode(mode: str) -> LiveOntogenesisProfile:
    p = default_ontogenesis_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    if mode == LiveOntogenesisMode.BIRTH_LIMITED:
        p.purpose = "limited proto-concept birth from stable live candidates"
        p.allow_limited_birth = True
    elif mode == LiveOntogenesisMode.ONTOGENESIS_3D:
        p.purpose = "3-day bounded live ontogenesis (candidate + limited birth)"
        p.allow_limited_birth = True
    elif mode == LiveOntogenesisMode.ONTOGENESIS_7D:
        p.purpose = "7-day bounded live ontogenesis (candidate + limited birth)"
        p.allow_limited_birth = True
    elif mode == LiveOntogenesisMode.REPORT_ONLY:
        p.purpose = "rebuild ontogenesis reports from existing state only"
    elif mode == LiveOntogenesisMode.DOCTOR_ONLY:
        p.purpose = "validate ontogenesis prerequisites only"
    return p


def get_ontogenesis_profile(profile_id: Optional[str] = None,
                            ) -> LiveOntogenesisProfile:
    """Return the named profile, defaulting to the candidate-only one."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_ontogenesis_profile()
    for mode in LiveOntogenesisMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_ontogenesis_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default candidate-only ontogenesis profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in LiveOntogenesisMode.ALL]
