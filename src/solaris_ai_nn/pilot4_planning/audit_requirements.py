"""Pilot-4 external-actuation audit requirements -- schema only.

The :class:`AuditChecklist` specifies the audit fields any future external
action would have to record. The current system continues to audit
simulated/dry-run actions only; this external-audit schema is specification
only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


# The fields a future external-action audit record would require.
REQUIRED_AUDIT_FIELDS = (
    "action_proposal", "source_desire", "executive_decision",
    "governance_approval", "safety_decision", "firewall_decision",
    "consent_reference", "target", "expected_effect", "actual_effect",
    "timestamp", "rollback_undo_status", "human_reviewer", "emergency_state",
    "evidence_refs",
)


@dataclass
class ExternalActuationAuditRequirement:
    """One required audit field for a future external action."""

    field_name: str
    description: str
    mandatory: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AuditChecklist:
    """The external-actuation audit schema (specification only)."""

    requirements: List[ExternalActuationAuditRequirement] = field(
        default_factory=list)
    applies_to_current_system: bool = False

    def __post_init__(self) -> None:
        if not self.requirements:
            self.requirements = [
                ExternalActuationAuditRequirement(
                    field_name=f, description=f.replace("_", " "))
                for f in REQUIRED_AUDIT_FIELDS]
        # The external schema does not apply to the current system, which
        # audits simulated/dry-run actions only.
        self.applies_to_current_system = False

    def field_names(self) -> List[str]:
        return [r.field_name for r in self.requirements]

    def has_field(self, name: str) -> bool:
        return any(r.field_name == name for r in self.requirements)

    @property
    def completeness(self) -> float:
        return 1.0 if self.requirements else 0.0

    def snapshot(self) -> Dict[str, Any]:
        return {
            "field_count": len(self.requirements),
            "fields": self.field_names(),
            "applies_to_current_system": False,
            "note": "external-audit schema is specification only; the current "
                    "system audits simulated/dry-run actions only",
        }

    def to_dict(self) -> Dict[str, Any]:
        return {"requirements": [r.to_dict() for r in self.requirements],
                "applies_to_current_system": False}
