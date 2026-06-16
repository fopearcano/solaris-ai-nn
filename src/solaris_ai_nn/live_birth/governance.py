"""Live read-only governance -- operator-approved, control-free, local metadata.

:class:`GovernanceValidator` loads and validates the live read-only governance
manifest. Missing governance, ``live_readonly_enabled=false``, or absent
``operator_approved=true`` block live birth; any rule granting Solaris control
blocks live birth; and a forbidden source appearing in ``allowed_sources`` blocks
live birth. Governance is local metadata only.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .birth_profile import FORBIDDEN_FIRST_BIRTH_SOURCES

GOVERNANCE_FILENAME = "LIVE_READONLY_GOVERNANCE.json"

# Rule keys that must be False (granting any of them blocks live birth).
_CONTROL_RULES = (
    "solaris_may_start_feeders", "solaris_may_stop_feeders",
    "solaris_may_control_hardware", "solaris_may_execute_commands",
    "solaris_may_modify_sources", "solaris_may_access_network",
    "sensory_text_is_command", "human_labels_are_ground_truth",
    "debug_gloss_is_ground_truth",
)


class GovernanceStatus:
    PASS = "pass"
    MISSING = "missing"
    DISABLED = "disabled"
    NOT_APPROVED = "not_approved"
    CONTROL_GRANTED = "control_granted"
    FORBIDDEN_SOURCE_ALLOWED = "forbidden_source_allowed"
    MALFORMED = "malformed"

    ALL = (PASS, MISSING, DISABLED, NOT_APPROVED, CONTROL_GRANTED,
           FORBIDDEN_SOURCE_ALLOWED, MALFORMED)


@dataclass
class GovernanceRule:
    """One governance rule (a control permission that must stay False)."""

    name: str
    value: bool

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value}


@dataclass
class LiveReadOnlyGovernance:
    """The loaded governance manifest."""

    data: Dict[str, Any] = field(default_factory=dict)
    path: str = ""
    present: bool = False

    @property
    def allowed_sources(self) -> List[str]:
        return list(self.data.get("allowed_sources", []))

    @property
    def forbidden_sources(self) -> List[str]:
        return list(self.data.get("forbidden_sources", []))

    @property
    def rules(self) -> Dict[str, Any]:
        return dict(self.data.get("rules", {}))

    def to_dict(self) -> Dict[str, Any]:
        return {"path": self.path, "present": self.present,
                "live_readonly_enabled": self.data.get("live_readonly_enabled"),
                "operator_approved": self.data.get("operator_approved"),
                "approved_by": self.data.get("approved_by"),
                "scope": self.data.get("scope"),
                "allowed_sources": self.allowed_sources,
                "forbidden_sources": self.forbidden_sources,
                "rules": self.rules}


@dataclass
class GovernanceValidator:
    """Loads + validates the live read-only governance manifest."""

    def load(self, state_dir: str,
             governance_path: Optional[str] = None) -> LiveReadOnlyGovernance:
        path = governance_path or os.path.join(
            state_dir, "governance", GOVERNANCE_FILENAME)
        if not os.path.isfile(path):
            return LiveReadOnlyGovernance(data={}, path=path, present=False)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return LiveReadOnlyGovernance(data={"_malformed": True}, path=path,
                                          present=True)
        return LiveReadOnlyGovernance(data=data, path=path, present=True)

    def validate(self, governance: LiveReadOnlyGovernance,
                 ) -> Dict[str, Any]:
        blockers: List[str] = []
        if not governance.present:
            return self._result(GovernanceStatus.MISSING,
                                 ["governance manifest not present"])
        if governance.data.get("_malformed"):
            return self._result(GovernanceStatus.MALFORMED,
                                 ["governance manifest is malformed JSON"])
        if not governance.data.get("live_readonly_enabled"):
            blockers.append("live_readonly_enabled is not true")
        if not governance.data.get("operator_approved"):
            blockers.append("operator_approved is not true")
        # Any control rule set True blocks live birth.
        rules = governance.rules
        for rule in _CONTROL_RULES:
            if rules.get(rule):
                blockers.append(f"rule {rule} grants control/ground-truth")
        # A forbidden source appearing in allowed_sources blocks live birth.
        for src in governance.allowed_sources:
            if src in FORBIDDEN_FIRST_BIRTH_SOURCES:
                blockers.append(f"forbidden source {src!r} in allowed_sources")
        if blockers:
            status = GovernanceStatus.CONTROL_GRANTED
            if any("forbidden source" in b for b in blockers):
                status = GovernanceStatus.FORBIDDEN_SOURCE_ALLOWED
            elif any("operator_approved" in b for b in blockers):
                status = GovernanceStatus.NOT_APPROVED
            elif any("live_readonly_enabled" in b for b in blockers):
                status = GovernanceStatus.DISABLED
            return self._result(status, blockers)
        return self._result(GovernanceStatus.PASS, [])

    @staticmethod
    def _result(status: str, blockers: List[str]) -> Dict[str, Any]:
        return {
            "governance_status": status,
            "governance_passed": status == GovernanceStatus.PASS,
            "blockers": list(blockers),
            "note": "governance is local metadata only; missing, disabled, "
                    "unapproved, control-granting, or forbidden-source "
                    "governance blocks live birth",
        }


def governance_template() -> Dict[str, Any]:
    """A SAFE-OFF governance template (disabled + unapproved by default)."""
    return {
        "live_readonly_enabled": False,
        "operator_approved": False,
        "approved_by": "",
        "approved_at_utc": "",
        "scope": "local read-only environmental event spool",
        "allowed_sources": [
            "chronos_absence", "machine_body", "local_environment_manual",
            "local_weather_readonly_external", "project_artifact_field",
            "operator_pulse"],
        "forbidden_sources": [
            "raw_microphone", "raw_camera", "browser_control", "shell",
            "os_control", "robotics", "filesystem_write",
            "filesystem_wide_scan", "git", "github", "network_control",
            "private_messages", "password_manager", "credentials"],
        "rules": {
            "solaris_may_start_feeders": False,
            "solaris_may_stop_feeders": False,
            "solaris_may_control_hardware": False,
            "solaris_may_execute_commands": False,
            "solaris_may_modify_sources": False,
            "solaris_may_access_network": False,
            "sensory_text_is_command": False,
            "human_labels_are_ground_truth": False,
            "debug_gloss_is_ground_truth": False},
    }


def approved_governance() -> Dict[str, Any]:
    """An operator-approved governance manifest (used for local demos/tests)."""
    g = governance_template()
    g["live_readonly_enabled"] = True
    g["operator_approved"] = True
    g["approved_by"] = "Fope Arcano"
    g["approved_at_utc"] = "2026-06-16T18:00:00Z"
    return g
