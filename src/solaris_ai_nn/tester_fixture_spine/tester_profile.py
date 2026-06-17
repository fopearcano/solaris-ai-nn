"""Tester fixture profile -- bounded, fixture-only, membrane-based demo config.

:class:`TesterFixtureProfile` describes a bounded tester demo run. The default profile
(``fixture_tester_v0``) is fixture-only, deterministic, requires the environmental
membrane and sensory impressions, allows raw-event fallback only when the membrane is
unavailable (and only if explicitly reported), forbids any raw-event downstream
promotion, requires no live governance and no external feeders, and never controls
feeders/hardware/network/Git/GitHub or treats tester feedback as training.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class TesterFixtureMode:
    FIXTURE_TESTER = "fixture_tester"
    FIXTURE_MEMBRANE_ONLY = "fixture_membrane_only"
    FIXTURE_OBSERVATION_ONLY = "fixture_observation_only"
    FIXTURE_ONTOGENESIS_LIMITED = "fixture_ontogenesis_limited"
    FIXTURE_SEMIOGENESIS_LIMITED = "fixture_semiogenesis_limited"
    FIXTURE_COGNITION_LIMITED = "fixture_cognition_limited"
    FIXTURE_CLAIMS_ONLY = "fixture_claims_only"
    FIXTURE_REGRESSION_ONLY = "fixture_regression_only"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (FIXTURE_TESTER, FIXTURE_MEMBRANE_ONLY, FIXTURE_OBSERVATION_ONLY,
           FIXTURE_ONTOGENESIS_LIMITED, FIXTURE_SEMIOGENESIS_LIMITED,
           FIXTURE_COGNITION_LIMITED, FIXTURE_CLAIMS_ONLY,
           FIXTURE_REGRESSION_ONLY, REPORT_ONLY, DOCTOR_ONLY)

    # Modes that enable an optional learning stage in the golden run.
    WITH_ONTOGENESIS = (FIXTURE_TESTER, FIXTURE_ONTOGENESIS_LIMITED,
                        FIXTURE_SEMIOGENESIS_LIMITED, FIXTURE_COGNITION_LIMITED)
    WITH_SEMIOGENESIS = (FIXTURE_TESTER, FIXTURE_SEMIOGENESIS_LIMITED,
                         FIXTURE_COGNITION_LIMITED)
    WITH_COGNITION = (FIXTURE_TESTER, FIXTURE_COGNITION_LIMITED)


class TesterFixtureConstraint:
    FIXTURE_ONLY = "fixture_only"
    DETERMINISTIC_INPUT = "deterministic_input"
    BOUNDED_RUNTIME = "bounded_runtime"
    NO_LIVE_EVENTS = "no_live_events"
    NO_EXTERNAL_FEEDERS = "no_external_feeders"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    NO_NETWORK_SHELL_GIT = "no_network_shell_browser_os_git_github"
    NO_PUBLISH_UPLOAD = "no_publication_or_upload"
    NO_ACTUATION = "no_real_world_actuation"
    MEMBRANE_REQUIRED = "membrane_required"
    IMPRESSIONS_REQUIRED = "sensory_impressions_required"
    RAW_FALLBACK_ONLY_IF_NO_MEMBRANE = \
        "raw_fallback_allowed_only_if_membrane_unavailable_and_reported"
    NO_RAW_DOWNSTREAM_PROMOTION = "no_downstream_raw_event_promotion"
    NO_UNSUPPORTED_CLAIMS = "no_unsupported_claims"
    CLAIMGUARD_IF_AVAILABLE = "claimguard_or_equivalent_scan_if_available"
    TESTER_FEEDBACK_NOT_TRAINING = "tester_feedback_not_training"

    ALL = (FIXTURE_ONLY, DETERMINISTIC_INPUT, BOUNDED_RUNTIME, NO_LIVE_EVENTS,
           NO_EXTERNAL_FEEDERS, NO_FEEDER_CONTROL, NO_HARDWARE_CONTROL,
           NO_NETWORK_SHELL_GIT, NO_PUBLISH_UPLOAD, NO_ACTUATION,
           MEMBRANE_REQUIRED, IMPRESSIONS_REQUIRED,
           RAW_FALLBACK_ONLY_IF_NO_MEMBRANE, NO_RAW_DOWNSTREAM_PROMOTION,
           NO_UNSUPPORTED_CLAIMS, CLAIMGUARD_IF_AVAILABLE,
           TESTER_FEEDBACK_NOT_TRAINING)


DEFAULT_PROFILE_ID = "fixture_tester_v0"


@dataclass
class TesterFixtureProfile:
    """A bounded, fixture-only tester demo profile (membrane-based, read-only)."""

    profile_id: str
    purpose: str
    mode: str = TesterFixtureMode.FIXTURE_TESTER
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 120.0
    max_events: int = 500
    require_membrane: bool = True
    require_impressions: bool = True
    allow_raw_fallback_if_no_membrane: bool = True
    run_ontogenesis: bool = True
    run_semiogenesis: bool = True
    run_cognition: bool = True
    run_claims: bool = True
    governance_required: bool = False
    feeders_required: bool = False
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in TesterFixtureMode.ALL:
            self.mode = TesterFixtureMode.FIXTURE_TESTER
        # Optional-stage gating per mode (modes skip honestly, never silently).
        self.run_ontogenesis = self.mode in TesterFixtureMode.WITH_ONTOGENESIS
        self.run_semiogenesis = self.mode in TesterFixtureMode.WITH_SEMIOGENESIS
        self.run_cognition = self.mode in TesterFixtureMode.WITH_COGNITION
        self.run_claims = self.mode not in (
            TesterFixtureMode.FIXTURE_MEMBRANE_ONLY,
            TesterFixtureMode.FIXTURE_OBSERVATION_ONLY)
        if self.mode == TesterFixtureMode.FIXTURE_CLAIMS_ONLY:
            self.run_claims = True
        # Governance/feeders are never required in fixture-only tester mode.
        self.governance_required = False
        self.feeders_required = False

    @property
    def is_report_only(self) -> bool:
        return self.mode == TesterFixtureMode.REPORT_ONLY

    @property
    def is_doctor_only(self) -> bool:
        return self.mode == TesterFixtureMode.DOCTOR_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s, "max_events": self.max_events,
            "require_membrane": self.require_membrane,
            "require_impressions": self.require_impressions,
            "allow_raw_fallback_if_no_membrane":
                self.allow_raw_fallback_if_no_membrane,
            "run_ontogenesis": self.run_ontogenesis,
            "run_semiogenesis": self.run_semiogenesis,
            "run_cognition": self.run_cognition, "run_claims": self.run_claims,
            "governance_required": self.governance_required,
            "feeders_required": self.feeders_required,
            "fixture_only": True, "requires_live_data": False,
            "limitations": list(self.limitations),
        }


def default_tester_profile() -> TesterFixtureProfile:
    """The default tester demo profile (fixture-only, membrane-based)."""
    return TesterFixtureProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("a fixture-only, deterministic, bounded tester demo: run a "
                 "known-good organismic rehearsal (validation/quarantine -> "
                 "environmental membrane -> sensory impressions -> membrane "
                 "integration audit -> observation -> optional ontogenesis/"
                 "semiogenesis/cognition -> claim/safety scan), build a local "
                 "artifact bundle, and check reproducibility/regression -- "
                 "reproducibility and tester confidence, not impressive "
                 "cognition"),
        mode=TesterFixtureMode.FIXTURE_TESTER,
        constraints=list(TesterFixtureConstraint.ALL),
        max_runtime_s=120.0, max_events=500,
        limitations=[
            "fixture-only by default; no live data, governance, or feeders "
            "are required",
            "the environmental membrane is required; downstream learning "
            "stages consume sensory impressions, never raw events",
            "raw-event fallback is allowed only when the membrane is "
            "unavailable and is loudly reported",
            "optional ontogenesis/semiogenesis/cognition stages skip honestly "
            "with an explicit marker when unavailable or disabled",
            "the tester bundle is local-only; nothing is published or uploaded "
            "and tester feedback is never used as training",
            "fixture success is a reproducibility signal, not evidence of "
            "consciousness/life/agency"])


def _profile_for_mode(mode: str) -> TesterFixtureProfile:
    p = default_tester_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    p.__post_init__()
    purposes = {
        TesterFixtureMode.FIXTURE_MEMBRANE_ONLY:
            "fixture-only membrane stage (impressions only; no downstream)",
        TesterFixtureMode.FIXTURE_OBSERVATION_ONLY:
            "fixture-only membrane + observation (impression diet only)",
        TesterFixtureMode.FIXTURE_ONTOGENESIS_LIMITED:
            "fixture-only through limited ontogenesis from impressions",
        TesterFixtureMode.FIXTURE_SEMIOGENESIS_LIMITED:
            "fixture-only through limited semiogenesis (ancestry preserved)",
        TesterFixtureMode.FIXTURE_COGNITION_LIMITED:
            "fixture-only through limited cognition (ancestry preserved)",
        TesterFixtureMode.FIXTURE_CLAIMS_ONLY:
            "fixture-only claim/safety scan over existing artifacts",
        TesterFixtureMode.FIXTURE_REGRESSION_ONLY:
            "fixture-only regression check against the golden baseline",
        TesterFixtureMode.REPORT_ONLY:
            "rebuild tester reports from existing tester state only",
        TesterFixtureMode.DOCTOR_ONLY:
            "validate tester prerequisites only (no demo run)",
    }
    if mode in purposes:
        p.purpose = purposes[mode]
    return p


def get_tester_profile(profile_id: Optional[str] = None) -> TesterFixtureProfile:
    """Return the named tester profile, defaulting to ``fixture_tester_v0``."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_tester_profile()
    for mode in TesterFixtureMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_tester_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default fixture tester profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in TesterFixtureMode.ALL]
