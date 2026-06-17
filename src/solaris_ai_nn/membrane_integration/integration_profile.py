"""Membrane integration profile -- bounded, read-only audit/enforcement config.

:class:`MembraneIntegrationProfile` describes a bounded integration run. The default
profile (``membrane_integration_v0``) requires the membrane when available, allows raw
event fallback only in fixture/demo or explicit fallback mode (and loudly reports it),
requires live ontogenesis to prefer sensory impressions, requires semiogenesis and
cognition to preserve impression ancestry, and forbids any raw-event direct path into
concept/sign/cognition birth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class MembraneIntegrationMode:
    FIXTURE_INTEGRATION = "fixture_integration"
    LIVE_INTEGRATION_AUDIT = "live_integration_audit"
    LIVE_INTEGRATION_ENFORCED = "live_integration_enforced"
    REPORT_ONLY = "report_only"
    DOCTOR_ONLY = "doctor_only"

    ALL = (FIXTURE_INTEGRATION, LIVE_INTEGRATION_AUDIT,
           LIVE_INTEGRATION_ENFORCED, REPORT_ONLY, DOCTOR_ONLY)

    LIVE = (LIVE_INTEGRATION_AUDIT, LIVE_INTEGRATION_ENFORCED)


class MembraneIntegrationConstraint:
    MEMBRANE_REQUIRED_WHEN_AVAILABLE = "membrane_required_when_available"
    RAW_FALLBACK_LIMITED = "raw_fallback_allowed_only_fixture_or_explicit"
    FALLBACK_LOUDLY_REPORTED = "fallback_must_be_loudly_reported"
    ONTOGENESIS_PREFERS_IMPRESSIONS = "ontogenesis_must_prefer_impressions"
    SEMIOGENESIS_PRESERVES_ANCESTRY = "semiogenesis_must_preserve_ancestry"
    COGNITION_PRESERVES_ANCESTRY = "cognition_must_preserve_ancestry"
    NO_RAW_DIRECT_BIRTH = "no_raw_event_direct_path_into_birth"
    GOVERNANCE_REQUIRED_LIVE = "governance_required_for_live_mode"
    NO_FEEDER_CONTROL = "no_feeder_control"
    NO_HARDWARE_CONTROL = "no_hardware_control"
    NO_NETWORK_SHELL_GIT = "no_network_shell_browser_os_git_github"
    BOUNDED_RUNTIME = "bounded_runtime"
    NO_UNSUPPORTED_CLAIMS = "no_unsupported_claims"

    ALL = (MEMBRANE_REQUIRED_WHEN_AVAILABLE, RAW_FALLBACK_LIMITED,
           FALLBACK_LOUDLY_REPORTED, ONTOGENESIS_PREFERS_IMPRESSIONS,
           SEMIOGENESIS_PRESERVES_ANCESTRY, COGNITION_PRESERVES_ANCESTRY,
           NO_RAW_DIRECT_BIRTH, GOVERNANCE_REQUIRED_LIVE, NO_FEEDER_CONTROL,
           NO_HARDWARE_CONTROL, NO_NETWORK_SHELL_GIT, BOUNDED_RUNTIME,
           NO_UNSUPPORTED_CLAIMS)


DEFAULT_PROFILE_ID = "membrane_integration_v0"


@dataclass
class MembraneIntegrationProfile:
    """A bounded membrane-integration profile (audit/enforcement, read-only)."""

    profile_id: str
    purpose: str
    mode: str = MembraneIntegrationMode.LIVE_INTEGRATION_AUDIT
    constraints: List[str] = field(default_factory=list)
    max_runtime_s: float = 120.0
    require_membrane: bool = True
    require_impressions: bool = False
    require_ancestry: bool = False
    allow_raw_fallback: bool = False
    governance_required: bool = True
    limitations: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.mode not in MembraneIntegrationMode.ALL:
            self.mode = MembraneIntegrationMode.LIVE_INTEGRATION_AUDIT
        if self.mode == MembraneIntegrationMode.FIXTURE_INTEGRATION:
            self.governance_required = False
            self.allow_raw_fallback = True
        if self.mode == MembraneIntegrationMode.LIVE_INTEGRATION_ENFORCED:
            self.require_impressions = True
            self.require_ancestry = True
            self.allow_raw_fallback = False

    @property
    def is_live(self) -> bool:
        return self.mode in MembraneIntegrationMode.LIVE

    @property
    def strict_enforced(self) -> bool:
        return self.mode == MembraneIntegrationMode.LIVE_INTEGRATION_ENFORCED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id, "purpose": self.purpose,
            "mode": self.mode, "is_live": self.is_live,
            "strict_enforced": self.strict_enforced,
            "constraints": list(self.constraints),
            "max_runtime_s": self.max_runtime_s,
            "require_membrane": self.require_membrane,
            "require_impressions": self.require_impressions,
            "require_ancestry": self.require_ancestry,
            "allow_raw_fallback": self.allow_raw_fallback,
            "governance_required": self.governance_required,
            "limitations": list(self.limitations),
        }


def default_integration_profile() -> MembraneIntegrationProfile:
    """The default membrane-integration profile (live audit, read-only)."""
    return MembraneIntegrationProfile(
        profile_id=DEFAULT_PROFILE_ID,
        purpose=("ensure live downstream modules consume membrane-filtered "
                 "sensory impressions rather than raw events: validate ancestry "
                 "chains, evaluate downstream contracts, detect bypasses, run "
                 "module adapters, and audit the live pipeline -- an "
                 "architectural audit/enforcement layer, not a new theory layer"),
        mode=MembraneIntegrationMode.LIVE_INTEGRATION_AUDIT,
        constraints=list(MembraneIntegrationConstraint.ALL),
        max_runtime_s=120.0, require_membrane=True, require_impressions=False,
        require_ancestry=False, allow_raw_fallback=False,
        governance_required=True,
        limitations=[
            "audit/enforcement only; the integration layer controls nothing",
            "raw events remain audit material; sensory impressions are the "
            "downstream perceptual material",
            "raw event fallback is allowed only in fixture/demo or explicit "
            "fallback mode and is loudly reported",
            "membrane bypass, missing ancestry, and contamination-propagation "
            "failures are detected and reported",
            "membrane integration is an architectural audit layer, not evidence "
            "of consciousness/life/agency"])


def _profile_for_mode(mode: str) -> MembraneIntegrationProfile:
    p = default_integration_profile()
    p.profile_id = f"{mode}_v0"
    p.mode = mode
    p.__post_init__()
    if mode == MembraneIntegrationMode.FIXTURE_INTEGRATION:
        p.purpose = "fixture-only membrane integration (raw fallback allowed)"
    elif mode == MembraneIntegrationMode.LIVE_INTEGRATION_ENFORCED:
        p.purpose = "enforced live integration (impressions + ancestry required)"
    elif mode == MembraneIntegrationMode.REPORT_ONLY:
        p.purpose = "rebuild integration reports from existing state only"
    elif mode == MembraneIntegrationMode.DOCTOR_ONLY:
        p.purpose = "validate integration prerequisites only"
    return p


def get_integration_profile(profile_id: Optional[str] = None,
                            ) -> MembraneIntegrationProfile:
    """Return the named profile, defaulting to the live-audit one."""
    if not profile_id or profile_id == DEFAULT_PROFILE_ID:
        return default_integration_profile()
    for mode in MembraneIntegrationMode.ALL:
        if profile_id in (mode, f"{mode}_v0"):
            return _profile_for_mode(mode)
    p = default_integration_profile()
    p.limitations.append(f"requested profile {profile_id!r} unknown; using the "
                         "default membrane-integration profile")
    return p


def available_profiles() -> List[str]:
    return [DEFAULT_PROFILE_ID] + [f"{m}_v0" for m in MembraneIntegrationMode.ALL]
