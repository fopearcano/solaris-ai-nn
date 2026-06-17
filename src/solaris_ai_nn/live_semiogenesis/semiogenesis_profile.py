"""Live semiogenesis profile -- bounded, read-only, conservative, candidate-first.

:class:`LiveSemiogenesisProfile` describes a bounded first live semiogenesis run. The
default profile (``live_semiogenesis_candidate_v0``) forms private sign *candidates*
only -- it does not enable full cognition, action-reaction learning, or developmental
autonomy. It requires governance, a birth certificate, an unblocked observation
stability gate, a live ontogenesis report, and live concept memory; only stable/born
proto-concepts can receive signs; signs must be private/internal identifiers; sign
birth requires utility evidence; and contaminated signs cannot be born.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LiveSemiogenesisMode:
    CANDIDATE_ONLY = "live_semiogenesis_candidate_only"
    BIRTH_LIMITED = "live_semiogenesis_birth_limited"
    SEMIOGENESIS_7D = "live_semiogenesis_7d"
    SEMIOGENESIS_14D = "live_semiogenesis_14d"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (CANDIDATE_ONLY, BIRTH_LIMITED, SEMIOGENESIS_7D, SEMIOGENESIS_14D,
           REPORT_ONLY, DOCTOR_ONLY)


class LiveSemiogenesisConstraint:
    LIVE_READONLY_ONLY = "live_read_only_only"
    GOVERNANCE_REQUIRED = "governance_required"
    BIRTH_CERTIFICATE_REQUIRED = "birth_certificate_required"
    OBSERVATION_STABILITY_REQUIRED = "observation_stability_gate_required"
    ONTOGENESIS_REPORT_REQUIRED = "live_ontogenesis_report_required"
    CONCEPT_MEMORY_REQUIRED = "live_concept_memory_required"
    ONLY_STABLE_CONCEPTS = "only_stable_or_born_proto_concepts_receive_signs"
    NO_FULL_COGNITION = "no_full_cognition_by_default"
    NO_ACTION_REACTION = "no_action_reaction_learning_by_default"
    NO_DEVELOPMENTAL_AUTONOMY = "no_developmental_autonomy_by_default"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    NO_NETWORK_SHELL_GIT = "no_network_shell_browser_os_git_github"
    BOUNDED_RUNTIME = "bounded_runtime"
    ACCEPTED_EVIDENCE_ONLY = "accepted_evidence_only"
    QUARANTINE_PRESERVED = "quarantine_preserved"
    OPERATOR_PULSE_WEIGHT_LIMITED = "operator_pulse_weight_limited"
    HUMAN_LABELS_NOT_GROUND_TRUTH = "human_labels_not_ground_truth"
    DEBUG_GLOSS_NOT_GROUND_TRUTH = "debug_gloss_not_ground_truth"
    SIGNS_PRIVATE_INTERNAL = "signs_must_be_private_internal_identifiers"
    UTILITY_EVIDENCE_REQUIRED = "sign_utility_evidence_required_for_sign_birth"
    CONTAMINATED_SIGNS_BLOCKED = "contaminated_signs_cannot_be_born"

    ALL = (LIVE_READONLY_ONLY, GOVERNANCE_REQUIRED, BIRTH_CERTIFICATE_REQUIRED,
           OBSERVATION_STABILITY_REQUIRED, ONTOGENESIS_REPORT_REQUIRED,
           CONCEPT_MEMORY_REQUIRED, ONLY_STABLE_CONCEPTS, NO_FULL_COGNITION,
           NO_ACTION_REACTION, NO_DEVELOPMENTAL_AUTONOMY, NO_FEEDER_CONTROL,
           NO_HARDWARE_CONTROL, NO_NETWORK_SHELL_GIT, BOUNDED_RUNTIME,
           ACCEPTED_EVIDENCE_ONLY, QUARANTINE_PRESERVED,
           OPERATOR_PULSE_WEIGHT_LIMITED, HUMAN_LABELS_NOT_GROUND_TRUTH,
           DEBUG_GLOSS_NOT_GROUND_TRUTH, SIGNS_PRIVATE_INTERNAL,
           UTILITY_EVIDENCE_REQUIRED, CONTAMINATED_SIGNS_BLOCKED)


DEFAULT_PROFILE_ID = "live_semiogenesis_candidate_v0"


@dataclass
class LiveSemiogenesisProfile:
    """A bounded first live semiogenesis profile (candidate-first, no cognition)."""

    profile_id: str
    purpose: str
    mode: str = LiveSemiogenesisMode.CANDIDATE_ONLY
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 180.0
    max_concepts: int = 200
    max_signs: int = 200
    min_utility: float = 0.6
    allow_limited_birth: bool = False
    cognition_enabled: bool = False
    action_reaction_enabled: bool = False
    developmental_autonomy_enabled: bool = False
    governance_required: bool = True
    birth_certificate_required: bool = True
    observation_stability_required: bool = True
    ontogenesis_report_required: bool = True
    concept_memory_required: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in LiveSemiogenesisMode.ALL:
            self.mode = LiveSemiogenesisMode.CANDIDATE_ONLY
        if self.mode in (LiveSemiogenesisMode.BIRTH_LIMITED,
                         LiveSemiogenesisMode.SEMIOGENESIS_7D,
                         LiveSemiogenesisMode.SEMIOGENESIS_14D):
            self.allow_limited_birth = True

    @property
    def candidate_only(self) -> bool:
        return not self.allow_limited_birth

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s,
            "max_concepts": self.max_concepts, "max_signs": self.max_signs,
            "min_utility": self.min_utility,
            "allow_limited_birth": self.allow_limited_birth,
            "candidate_only": self.candidate_only,
            "cognition_enabled": self.cognition_enabled,
            "action_reaction_enabled": self.action_reaction_enabled,
            "developmental_autonomy_enabled":
                self.developmental_autonomy_enabled,
            "governance_required": self.governance_required,
            "birth_certificate_required": self.birth_certificate_required,
            "observation_stability_required":
                self.observation_stability_required,
            "ontogenesis_report_required": self.ontogenesis_report_required,
            "concept_memory_required": self.concept_memory_required,
            "limitations": list(self.limitations),
        }


def default_semiogenesis_profile() -> LiveSemiogenesisProfile:
    """The default first-live-semiogenesis profile (candidates only, no cognition)."""
    return LiveSemiogenesisProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("form private internal signs over stable live proto-concepts: "
                 "generate private sign candidates, assess sign utility, build "
                 "private syntax relations, filter contamination, and gate sign "
                 "birth conservatively -- without full cognition, action-reaction "
                 "learning, or developmental autonomy"),
        mode=LiveSemiogenesisMode.CANDIDATE_ONLY,
        constraints=list(LiveSemiogenesisConstraint.ALL),
        max_runtime_s=180.0, max_concepts=200, max_signs=200, min_utility=0.6,
        allow_limited_birth=False, cognition_enabled=False,
        action_reaction_enabled=False, developmental_autonomy_enabled=False,
        governance_required=True, birth_certificate_required=True,
        observation_stability_required=True, ontogenesis_report_required=True,
        concept_memory_required=True,
        limitations=[
            "candidate-first; sign birth is conservative and gated",
            "no full cognition, no action-reaction learning, no developmental "
            "autonomy by default",
            "signs are private internal identifiers; human labels/gloss are "
            "never sign ground truth; operator pulse is stimulus, not teaching",
            "private syntax is operational relation structure, not language "
            "grammar or semantics",
            "private signs are not proof of language or understanding and prove "
            "nothing about consciousness/life/agency"])


def _profile_for_mode(mode: str) -> LiveSemiogenesisProfile:
    p = default_semiogenesis_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    if mode == LiveSemiogenesisMode.BIRTH_LIMITED:
        p.purpose = "limited private sign birth from stable proto-concepts"
        p.allow_limited_birth = True
    elif mode == LiveSemiogenesisMode.SEMIOGENESIS_7D:
        p.purpose = "7-day bounded live semiogenesis (candidate + limited birth)"
        p.allow_limited_birth = True
    elif mode == LiveSemiogenesisMode.SEMIOGENESIS_14D:
        p.purpose = "14-day bounded live semiogenesis (candidate + limited birth)"
        p.allow_limited_birth = True
    elif mode == LiveSemiogenesisMode.REPORT_ONLY:
        p.purpose = "rebuild semiogenesis reports from existing state only"
    elif mode == LiveSemiogenesisMode.DOCTOR_ONLY:
        p.purpose = "validate semiogenesis prerequisites only"
    return p


def get_semiogenesis_profile(profile_id: Optional[str] = None,
                             ) -> LiveSemiogenesisProfile:
    """Return the named profile, defaulting to the candidate-only one."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_semiogenesis_profile()
    for mode in LiveSemiogenesisMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_semiogenesis_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default candidate-only semiogenesis profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in LiveSemiogenesisMode.ALL]
