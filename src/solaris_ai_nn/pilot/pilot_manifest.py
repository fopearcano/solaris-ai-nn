"""PilotManifest -- the signed-off shape of one Pilot-0 run.

The manifest pins everything a reviewer needs: profile, operator, bounds,
input sources, output policy, features, governance approvals, and the
explicit :class:`PilotSafetyContract`. An unbounded pilot without governance
approval ids cannot even be constructed.
"""

from __future__ import annotations

import platform
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .profiles import PilotProfileType

DEFAULT_PILOT_FEATURES = {
    "plasticity": False, "plasticity_dry_run": False, "language": False,
    "embodiment": False, "sidecar": False, "evaluation": False,
    "local_status_server": False,
}


@dataclass
class PilotSafetyContract:
    """The explicit promises every pilot makes. All must hold to run."""

    read_only_external_world: bool = True
    simulation_only_actions: bool = True
    no_network_calls: bool = True
    no_os_commands: bool = True
    no_browser_automation: bool = True
    no_physical_actuation: bool = True
    no_committed_solaris_actions: bool = True
    no_source_code_rewriting: bool = True
    no_unbounded_run_without_approval: bool = True

    def violations(self) -> List[str]:
        return [name for name, value in self.__dict__.items() if not value]

    def is_intact(self) -> bool:
        return not self.violations()

    def statements(self) -> List[str]:
        """The contract, in words an operator signs off on."""
        return [
            "the external world is read-only: observed, never modified",
            "actions exist only inside the simulation",
            "no network calls",
            "no OS commands",
            "no browser automation",
            "no robotics or physical actuation",
            "no committed Solaris_Ai Actions (suggestions only)",
            "no source-code rewriting",
            "no unbounded run without explicit governance approval",
        ]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PilotEnvironment:
    """Where the pilot runs (captured for the record, not enforced)."""

    label: str = "local"
    description: str = "local research machine"
    platform: str = field(default_factory=platform.platform)
    python_version: str = field(default_factory=lambda: sys.version.split()[0])

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PilotManifest:
    """Pins one pilot run end to end."""

    profile: str = PilotProfileType.DEFAULT
    operator: str = ""
    state_dir: str = ".solaris_ai_nn_state/pilot"
    artifact_dir: str = ".solaris_ai_nn_pilots"
    input_sources: List[str] = field(default_factory=list)
    output_policy: str = "artifacts_only"  # never anything outward
    max_steps: Optional[int] = 300
    max_duration_s: Optional[float] = None
    substrate: str = "esn"
    enabled_features: Dict[str, bool] = field(
        default_factory=lambda: dict(DEFAULT_PILOT_FEATURES))
    governance_approval_ids: List[str] = field(default_factory=list)
    emergency_stop_path: str = ""
    expected_artifacts: List[str] = field(default_factory=list)
    notes: str = ""
    seed: int = 7
    pilot_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    created_at: float = field(default_factory=time.time)
    contract: PilotSafetyContract = field(default_factory=PilotSafetyContract)
    environment: PilotEnvironment = field(default_factory=PilotEnvironment)

    def __post_init__(self) -> None:
        if self.profile not in PilotProfileType.ALL:
            raise ValueError(f"unknown pilot profile {self.profile!r}; "
                             f"choose from {PilotProfileType.ALL}")
        if not self.is_bounded() and not self.governance_approval_ids:
            raise ValueError(
                "unbounded pilots require explicit governance approval ids "
                "(no pilot runs forever by default)")
        if not self.contract.is_intact():
            raise ValueError(
                "the pilot safety contract cannot be weakened: "
                f"{self.contract.violations()}")
        if not self.emergency_stop_path:
            from ..governance.emergency import sentinel_path

            self.emergency_stop_path = str(sentinel_path(self.state_dir))

    def is_bounded(self) -> bool:
        return self.max_steps is not None or self.max_duration_s is not None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pilot_id": self.pilot_id,
            "profile": self.profile,
            "created_at": self.created_at,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "operator": self.operator,
            "state_dir": self.state_dir,
            "artifact_dir": self.artifact_dir,
            "input_sources": list(self.input_sources),
            "output_policy": self.output_policy,
            "max_steps": self.max_steps,
            "max_duration_s": self.max_duration_s,
            "substrate": self.substrate,
            "enabled_features": dict(self.enabled_features),
            "governance_approval_ids": list(self.governance_approval_ids),
            "emergency_stop_path": self.emergency_stop_path,
            "expected_artifacts": list(self.expected_artifacts),
            "notes": self.notes,
            "seed": self.seed,
            "safety_contract": self.contract.to_dict(),
            "environment": self.environment.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PilotManifest":
        data = dict(data)
        contract = PilotSafetyContract(**{
            k: v for k, v in (data.pop("safety_contract", {}) or {}).items()
            if k in PilotSafetyContract.__dataclass_fields__})  # type: ignore[attr-defined]
        environment = PilotEnvironment(**{
            k: v for k, v in (data.pop("environment", {}) or {}).items()
            if k in PilotEnvironment.__dataclass_fields__})  # type: ignore[attr-defined]
        valid = set(cls.__dataclass_fields__) - {"contract", "environment"}  # type: ignore[attr-defined]
        return cls(contract=contract, environment=environment,
                   **{k: v for k, v in data.items() if k in valid})
