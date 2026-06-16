"""Alpha research profile -- the bounded, fixture-first run configuration.

:class:`AlphaResearchProfile` describes a bounded Alpha run: which modules it
enables, which state directories it needs, its runtime/tick budget, and its safety
constraints. The default profile (``alpha_fixture_e2e_v0``) is fixture-only: it
requires no live feeders, no network, and no Git/GitHub, and it never runs
unbounded. Live read-only profiles may exist as metadata but are blocked unless
governance artifacts exist.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AlphaProfileMode:
    FIXTURE_DEMO = "fixture_demo"
    SHORT_RESEARCH_CYCLE = "short_research_cycle"
    CLAIMS_ONLY = "claims_only"
    REVIEW_ONLY = "review_only"
    CYCLE_STATUS_ONLY = "cycle_status_only"
    DOCTOR_ONLY = "doctor_only"
    REPORT_ONLY = "report_only"

    ALL = (FIXTURE_DEMO, SHORT_RESEARCH_CYCLE, CLAIMS_ONLY, REVIEW_ONLY,
           CYCLE_STATUS_ONLY, DOCTOR_ONLY, REPORT_ONLY)


class AlphaProfileConstraint:
    FIXTURE_ONLY = "fixture_only"
    NO_LIVE_FEEDERS = "no_live_feeders"
    NO_NETWORK = "no_network"
    NO_GIT_GITHUB = "no_git_github"
    BOUNDED_RUNTIME = "bounded_runtime"
    NO_ACTUATION = "no_actuation"
    GOVERNANCE_REQUIRED_FOR_LIVE = "governance_required_for_live"

    ALL = (FIXTURE_ONLY, NO_LIVE_FEEDERS, NO_NETWORK, NO_GIT_GITHUB,
           BOUNDED_RUNTIME, NO_ACTUATION, GOVERNANCE_REQUIRED_FOR_LIVE)


# Default modules the fixture E2E demo will attempt (optional unless required).
_DEFAULT_ENABLED = (
    "plural_sensorium", "organismic_demo", "perceptual_metabolism",
    "perceptual_ontogenesis", "semiogenesis", "sensorium_cognition",
    "self_boundary", "desire_formation", "action_reaction",
    "developmental_life", "scientific_claims", "independent_review",
    "research_cycle",
)
_DEFAULT_OPTIONAL = (
    "live_field", "feeder_sdk", "sensorium_lab", "developmental_soak",
    "developmental_replication", "architecture_evolution", "experiment_compiler",
    "implementation_intake", "post_merge_assimilation", "research_baseline",
    "review_assimilation",
)
_DEFAULT_STATE_DIRS = ("input", "fixtures", "runs", "reports", "artifacts",
                       "claims", "review", "cycle", "logs", "index")


@dataclass
class AlphaResearchProfile:
    """A bounded Alpha run profile (fixture-first by default)."""

    profile_id: str
    purpose: str
    mode: str = AlphaProfileMode.FIXTURE_DEMO
    enabled_modules: List[str] = field(default_factory=list)
    optional_modules: List[str] = field(default_factory=list)
    required_state_dirs: List[str] = field(default_factory=list)
    max_runtime_s: float = 60.0
    max_ticks: int = 50
    fixture_mode_enabled: bool = True
    live_read_only_allowed: bool = False
    governance_required_for_live: bool = True
    safety_constraints: List[str] = field(default_factory=list)
    expected_artifacts: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in AlphaProfileMode.ALL:
            self.mode = AlphaProfileMode.FIXTURE_DEMO

    @property
    def is_fixture_only(self) -> bool:
        return self.fixture_mode_enabled and not self.live_read_only_allowed

    def live_blocked(self, governance_present: bool) -> bool:
        """Live read-only is blocked unless governance artifacts exist."""
        if not self.live_read_only_allowed:
            return True
        return not governance_present

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode,
            "enabled_modules": list(self.enabled_modules),
            "optional_modules": list(self.optional_modules),
            "required_state_dirs": list(self.required_state_dirs),
            "max_runtime_s": self.max_runtime_s, "max_ticks": self.max_ticks,
            "fixture_mode_enabled": self.fixture_mode_enabled,
            "live_read_only_allowed": self.live_read_only_allowed,
            "governance_required_for_live": self.governance_required_for_live,
            "is_fixture_only": self.is_fixture_only,
            "safety_constraints": list(self.safety_constraints),
            "expected_artifacts": list(self.expected_artifacts),
            "limitations": list(self.limitations),
        }


DEFAULT_PROFILE_ID = "alpha_fixture_e2e_v0"


def default_alpha_profile() -> AlphaResearchProfile:
    """The default fixture-only end-to-end Alpha profile."""
    return AlphaResearchProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("run a bounded, fixture-only end-to-end research path from "
                 "synthetic sensorium input to an alpha report, scientific "
                 "claims, review readiness, and a next action"),
        mode=AlphaProfileMode.FIXTURE_DEMO,
        enabled_modules=list(_DEFAULT_ENABLED),
        optional_modules=list(_DEFAULT_OPTIONAL),
        required_state_dirs=list(_DEFAULT_STATE_DIRS),
        max_runtime_s=60.0, max_ticks=50,
        fixture_mode_enabled=True, live_read_only_allowed=False,
        governance_required_for_live=True,
        safety_constraints=[
            AlphaProfileConstraint.FIXTURE_ONLY,
            AlphaProfileConstraint.NO_LIVE_FEEDERS,
            AlphaProfileConstraint.NO_NETWORK,
            AlphaProfileConstraint.NO_GIT_GITHUB,
            AlphaProfileConstraint.BOUNDED_RUNTIME,
            AlphaProfileConstraint.NO_ACTUATION,
            AlphaProfileConstraint.GOVERNANCE_REQUIRED_FOR_LIVE],
        expected_artifacts=[
            "ALPHA_STATE_MANIFEST.json", "ALPHA_RESEARCH_SYSTEM_REPORT.md",
            "ALPHA_ARTIFACT_INDEX.json", "ALPHA_OPERATOR_RUNBOOK.md"],
        limitations=[
            "fixture-only; no live data and no feeders",
            "optional modules may be skipped and are reported honestly",
            "alpha is local research orchestration, not a product release",
            "no consciousness/life/agency evidence is produced or claimed"])


def _profile_for_mode(mode: str) -> AlphaResearchProfile:
    p = default_alpha_profile()
    p.profile_id = f"alpha_{mode}_v0"
    p.mode = mode
    if mode == AlphaProfileMode.CLAIMS_ONLY:
        p.purpose = "generate a scientific claim summary only (fixture-safe)"
        p.enabled_modules = ["scientific_claims"]
    elif mode == AlphaProfileMode.REVIEW_ONLY:
        p.purpose = "generate an independent review mini-pack only (fixture-safe)"
        p.enabled_modules = ["independent_review"]
    elif mode == AlphaProfileMode.CYCLE_STATUS_ONLY:
        p.purpose = "report the research cycle status only"
        p.enabled_modules = ["research_cycle"]
    elif mode == AlphaProfileMode.DOCTOR_ONLY:
        p.purpose = "run the system check (doctor) only"
        p.enabled_modules = []
    elif mode == AlphaProfileMode.REPORT_ONLY:
        p.purpose = "rebuild the alpha report from existing artifacts only"
        p.enabled_modules = []
    elif mode == AlphaProfileMode.SHORT_RESEARCH_CYCLE:
        p.purpose = "run a short fixture research cycle through claims and review"
    return p


# Profiles available as metadata (the default is fixture-only).
def get_alpha_profile(profile_id: Optional[str] = None) -> AlphaResearchProfile:
    """Return the named profile, defaulting to the fixture-only profile."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_alpha_profile()
    if profile_id == LIVE_READONLY_BIRTH_PROFILE_ID:
        # Live read-only birth is metadata-only here and is owned by the
        # live_birth package; it is blocked unless governance is present, and
        # the default alpha profile stays fixture-only. Asking the alpha layer
        # for it returns the fixture-only default with an explicit note.
        p = default_alpha_profile()
        p.limitations.append(
            "live_readonly_birth_v0 is a separate live read-only profile "
            "(see the live_birth package); it is blocked unless live governance "
            "is present and the default alpha profile remains fixture-only")
        return p
    for mode in AlphaProfileMode.ALL:
        if profile_id in (mode, f"alpha_{mode}_v0"):
            return _profile_for_mode(mode)
    # Unknown id -> safe default, but record the requested id in the purpose.
    p = default_alpha_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using "
                         "the default fixture-only profile")
    return p


# Metadata-only live read-only profile id (owned by the live_birth package).
LIVE_READONLY_BIRTH_PROFILE_ID = "live_readonly_birth_v0"


def available_profiles() -> List[str]:
    return ([DEFAULT_PROFILE_ID] + [f"alpha_{m}_v0" for m in AlphaProfileMode.ALL]
            + [LIVE_READONLY_BIRTH_PROFILE_ID])
