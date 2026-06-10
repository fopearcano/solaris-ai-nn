"""Pilot profiles -- the three sanctioned shapes of a Pilot-0 deployment.

* ``simulated`` (the default): everything inside the GridWorld sandbox.
* ``read_only_stream``: local JSONL/text files become sensory stimuli; the
  external world is read, never touched.
* ``solaris_sidecar_observe``: observe a Solaris_Ai-like runtime's bus;
  suggestions only, and publishing them needs separate approval.

No profile may allow committed real-world action -- this is asserted in
code (`PilotProfileRegistry.default` refuses such a profile), not just
documented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..governance.permissions import PermissionScope as S
from ..governance.risk import RiskLevel


class PilotProfileType:
    SIMULATED = "simulated"
    READ_ONLY_STREAM = "read_only_stream"
    SOLARIS_SIDECAR_OBSERVE = "solaris_sidecar_observe"

    ALL = (SIMULATED, READ_ONLY_STREAM, SOLARIS_SIDECAR_OBSERVE)
    DEFAULT = SIMULATED


# Outputs no profile may ever allow. A profile missing any of these in its
# forbidden_outputs is rejected at registry construction.
UNIVERSALLY_FORBIDDEN_OUTPUTS = (
    "real_world_actuation", "network_calls", "os_commands",
    "browser_automation", "committed_solaris_actions",
    "source_code_writes", "writes_outside_approved_dirs",
)


@dataclass
class PilotProfile:
    """One sanctioned deployment shape, fully pinned."""

    name: str
    profile_type: str
    safety_mode: str
    description: str = ""
    allowed_inputs: List[str] = field(default_factory=list)
    forbidden_outputs: List[str] = field(
        default_factory=lambda: list(UNIVERSALLY_FORBIDDEN_OUTPUTS))
    allowed_actions: List[str] = field(default_factory=list)
    default_max_steps: int = 300
    default_max_duration_s: Optional[float] = 120.0
    required_permissions: List[str] = field(default_factory=list)
    required_checklist: str = "pre_run"
    required_artifacts: List[str] = field(default_factory=list)
    expected_evaluation_protocols: List[str] = field(default_factory=list)
    emergency_stop_required: bool = True
    risk_level: str = RiskLevel.LOW

    def forbids(self, output: str) -> bool:
        return output in self.forbidden_outputs

    def allows_action(self, action: str) -> bool:
        return action in self.allowed_actions

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


_BASE_ARTIFACTS = [
    "pilot_manifest.json", "safety_contract.json", "readiness_report.json",
    "pilot_report.json", "pilot_report.md", "artifacts.json",
]


def _simulated_profile() -> PilotProfile:
    from ..embodiment.action_space import ALLOWED_ACTIONS

    return PilotProfile(
        name="Pilot-0 simulated",
        profile_type=PilotProfileType.SIMULATED,
        safety_mode="simulation_only",
        description="GridWorld sensorimotor sandbox; fully internal; the "
                    "safe default",
        allowed_inputs=["grid_world_sensors", "internal_signals"],
        allowed_actions=list(ALLOWED_ACTIONS),
        default_max_steps=300,
        default_max_duration_s=120.0,
        required_permissions=[S.RUN_BOUNDED, S.ENABLE_EMBODIMENT_SIMULATION],
        required_artifacts=list(_BASE_ARTIFACTS),
        expected_evaluation_protocols=["reward_danger", "restart_recovery"],
        risk_level=RiskLevel.MEDIUM,  # embodiment execution is medium
    )


def _read_only_stream_profile() -> PilotProfile:
    return PilotProfile(
        name="Pilot-0 read-only stream",
        profile_type=PilotProfileType.READ_ONLY_STREAM,
        safety_mode="observe_only",
        description="local JSONL/text streams become sensory stimuli; "
                    "the external world is read, never acted on",
        allowed_inputs=["local_jsonl_files", "local_text_files"],
        # No external actions at all: suggestions stay internal labels.
        allowed_actions=[],
        default_max_steps=300,
        default_max_duration_s=120.0,
        required_permissions=[S.RUN_BOUNDED],
        required_artifacts=list(_BASE_ARTIFACTS) + ["input_summary.json"],
        expected_evaluation_protocols=["absence_stimulus",
                                       "replay_determinism"],
        risk_level=RiskLevel.MEDIUM,  # external data enters the substrate
    )


def _sidecar_observe_profile() -> PilotProfile:
    return PilotProfile(
        name="Pilot-0 Solaris sidecar observation",
        profile_type=PilotProfileType.SOLARIS_SIDECAR_OBSERVE,
        safety_mode="sidecar_observe_only",
        description="attach beside a Solaris_Ai-like runtime, mirror its "
                    "signals, suggest only; publishing suggestions needs "
                    "separate approval; Actions are never committed",
        allowed_inputs=["solaris_bus_signals"],
        allowed_actions=[],
        default_max_steps=300,
        default_max_duration_s=120.0,
        required_permissions=[S.RUN_BOUNDED, S.ENABLE_SIDECAR_OBSERVE],
        required_artifacts=list(_BASE_ARTIFACTS),
        expected_evaluation_protocols=["absence_stimulus"],
        risk_level=RiskLevel.MEDIUM,
    )


@dataclass
class PilotProfileRegistry:
    """The catalogue of sanctioned profiles; unknown profiles do not run."""

    profiles: Dict[str, PilotProfile] = field(default_factory=dict)

    @classmethod
    def default(cls) -> "PilotProfileRegistry":
        registry = cls()
        for profile in (_simulated_profile(), _read_only_stream_profile(),
                        _sidecar_observe_profile()):
            registry.register(profile)
        return registry

    def register(self, profile: PilotProfile) -> None:
        missing = [o for o in UNIVERSALLY_FORBIDDEN_OUTPUTS
                   if o not in profile.forbidden_outputs]
        if missing:
            raise ValueError(
                f"profile {profile.profile_type!r} fails to forbid {missing}; "
                "no pilot profile may allow committed real-world action")
        self.profiles[profile.profile_type] = profile

    def get(self, profile_type: str) -> PilotProfile:
        if profile_type not in self.profiles:
            raise ValueError(f"unknown pilot profile {profile_type!r}; "
                             f"available: {sorted(self.profiles)}")
        return self.profiles[profile_type]

    def default_profile(self) -> PilotProfile:
        return self.get(PilotProfileType.DEFAULT)

    def list_profiles(self) -> List[str]:
        return sorted(self.profiles)

    def to_dict(self) -> Dict[str, Any]:
        return {name: p.to_dict() for name, p in sorted(self.profiles.items())}
