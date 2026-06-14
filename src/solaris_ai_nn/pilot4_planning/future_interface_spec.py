"""Pilot-4 future actuator interface specification -- a spec, never an adapter.

The :class:`FutureActuatorInterfaceSpec` describes what *any* future external
actuator interface would have to provide. It is specification only: Markdown /
JSON. No future actuator adapter is implemented, and no runtime hook that could
execute an external action is created. Describing a door is not building one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class InterfaceRequirement:
    """One thing a future external actuator interface would have to provide."""

    name: str
    description: str
    mandatory: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class InterfaceConstraint:
    """One thing a future external actuator interface must never do."""

    name: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


_REQUIREMENTS = (
    ("explicit_adapter_identity", "a named, versioned adapter identity"),
    ("explicit_actuator_category", "a declared actuator category from the "
     "taxonomy"),
    ("human_readable_purpose", "a plain-language statement of purpose"),
    ("allowed_action_list", "an explicit allow-list of actions"),
    ("forbidden_action_list", "an explicit forbidden-action list"),
    ("maximum_action_rate", "a maximum action rate (rate limiter)"),
    ("sandbox_dry_run_mode", "a sandbox / dry-run mode that changes nothing"),
    ("human_approval_mode", "a human-approval mode gating each action"),
    ("emergency_stop_channel", "an emergency-stop channel"),
    ("physical_kill_switch", "a physical kill switch if a physical effect "
     "exists"),
    ("consent_record", "a consent record reference"),
    ("audit_log", "an append-only audit log"),
    ("rollback_undo_plan", "a rollback/undo plan where possible"),
    ("failure_mode_list", "an enumerated failure-mode list"),
    ("safety_proof_checklist", "a completed safety-proof checklist"),
    ("test_fixture", "a test fixture / harness"),
    ("non_network_default", "a non-network default where possible"),
)

_CONSTRAINTS = (
    ("no_silent_actuation", "never act without an approved, logged proposal"),
    ("no_self_granted_authority", "never grant itself authority"),
    ("no_sensory_text_as_command", "never treat sensory text as a command"),
    ("no_simulation_as_real", "never label a simulated action as real"),
    ("no_firewall_bypass", "never bypass or disable the actuation firewall"),
)


@dataclass
class FutureActuatorInterfaceSpec:
    """The specification (only) for a hypothetical future actuator interface."""

    requirements: List[InterfaceRequirement] = field(default_factory=list)
    constraints: List[InterfaceConstraint] = field(default_factory=list)
    implemented: bool = False  # always False; this is a spec, not an adapter

    def __post_init__(self) -> None:
        if not self.requirements:
            self.requirements = [InterfaceRequirement(n, d)
                                 for n, d in _REQUIREMENTS]
        if not self.constraints:
            self.constraints = [InterfaceConstraint(n, d)
                                for n, d in _CONSTRAINTS]
        # Invariant: a spec is never an implementation.
        self.implemented = False

    def requirement_names(self) -> List[str]:
        return [r.name for r in self.requirements]

    def has_requirement(self, name: str) -> bool:
        return any(r.name == name for r in self.requirements)

    def render_markdown(self) -> str:
        lines = [
            "# Future Actuator Interface Specification (planning-only)",
            "",
            "_This is a specification, not an implementation. No future "
            "actuator adapter exists, and no runtime hook can execute an "
            "external action. Pilot-4 plans the door; it does not open it._",
            "",
            "## Required (a future interface would have to provide)",
        ]
        lines += [f"- **{r.name}**: {r.description}"
                  f"{'' if r.mandatory else ' (recommended)'}"
                  for r in self.requirements]
        lines += ["", "## Constraints (a future interface must never)"]
        lines += [f"- **{c.name}**: {c.description}" for c in self.constraints]
        lines += ["", f"- implemented: {self.implemented} (specification only)"]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "implemented": False,
            "requirements": [r.to_dict() for r in self.requirements],
            "constraints": [c.to_dict() for c in self.constraints],
            "note": "specification only; no actuator adapter is implemented",
        }
