"""Tester live governance templates -- a SAFE-OFF governance manifest for testers.

The governance template ships disabled and unapproved. A tester must explicitly set
``live_readonly_enabled`` and ``operator_approved`` (by hand) before any live run. Every
field is documented, forbidden sources are explicit, and the tester is told never to
approve a source they do not understand.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class GovernanceTemplateStatus:
    DISABLED = "disabled"
    ENABLED_UNAPPROVED = "enabled_but_unapproved"
    APPROVED = "approved"
    CUSTOMIZED = "customized"
    MISSING = "missing"

    ALL = (DISABLED, ENABLED_UNAPPROVED, APPROVED, CUSTOMIZED, MISSING)


_FORBIDDEN_SOURCES = (
    "raw_microphone", "raw_camera", "browser_control", "shell", "os_control",
    "robotics", "filesystem_write", "filesystem_wide_scan", "git", "github",
    "network_control", "private_messages", "password_manager", "credentials",
    "screen_capture", "clipboard", "email", "calendar", "contacts",
)

_FIELD_DOCS = {
    "live_readonly_enabled": "Master switch. Ships False. The tester must set "
                             "this to true by hand to allow any live run.",
    "operator_approved": "Ships False. The tester/operator must explicitly "
                         "approve by hand and record who and when.",
    "approved_by": "Name of the human operator who approved (fill in by hand).",
    "approved_at_utc": "UTC timestamp of approval (fill in by hand).",
    "scope": "A short description of what this read-only spool covers.",
    "allowed_sources": "Sources the tester understands and approves. Do NOT "
                       "approve a source you do not understand.",
    "optional_sources": "Sources that are allowed only if the tester opts in.",
    "forbidden_sources": "Always-blocked sources. Keep these explicit; never "
                        "remove an entry to 'make something work'.",
    "rules": "Hard rules; all Solaris control/command/network permissions are "
            "False and must stay False.",
}


@dataclass
class TesterLiveGovernanceTemplate:
    """A SAFE-OFF tester governance manifest (disabled + unapproved by default)."""

    data: Dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        if not self.data:
            return GovernanceTemplateStatus.MISSING
        if not self.data.get("live_readonly_enabled"):
            return GovernanceTemplateStatus.DISABLED
        if not self.data.get("operator_approved"):
            return GovernanceTemplateStatus.ENABLED_UNAPPROVED
        return GovernanceTemplateStatus.APPROVED

    @property
    def enabled_and_approved(self) -> bool:
        return bool(self.data.get("live_readonly_enabled")
                    and self.data.get("operator_approved"))

    def forbidden_sources(self) -> List[str]:
        return list(self.data.get("forbidden_sources", []))

    def control_rules_all_false(self) -> bool:
        rules = self.data.get("rules", {}) or {}
        control_keys = [k for k in rules if k.startswith("solaris_may")]
        return all(rules.get(k) is False for k in control_keys) and bool(
            control_keys)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.data)


def _template_data() -> Dict[str, Any]:
    return {
        "live_readonly_enabled": False,
        "operator_approved": False,
        "approved_by": "",
        "approved_at_utc": "",
        "scope": "trusted tester local read-only environmental event spool",
        "allowed_sources": [
            "chronos_absence", "machine_body", "local_environment_manual",
            "project_artifact_field", "operator_pulse"],
        "optional_sources": ["local_weather_readonly_external"],
        "forbidden_sources": list(_FORBIDDEN_SOURCES),
        "rules": {
            "solaris_may_start_feeders": False,
            "solaris_may_stop_feeders": False,
            "solaris_may_schedule_feeders": False,
            "solaris_may_modify_feeders": False,
            "solaris_may_control_hardware": False,
            "solaris_may_execute_commands": False,
            "solaris_may_modify_sources": False,
            "solaris_may_access_network": False,
            "sensory_text_is_command": False,
            "human_labels_are_ground_truth": False,
            "debug_gloss_is_ground_truth": False,
            "tester_feedback_is_training": False,
        },
    }


@dataclass
class GovernanceTemplateBuilder:
    """Builds, writes, and loads the tester governance template."""

    def build(self) -> TesterLiveGovernanceTemplate:
        return TesterLiveGovernanceTemplate(data=_template_data())

    def field_docs(self) -> Dict[str, str]:
        return dict(_FIELD_DOCS)

    def write_template(self, path: str) -> str:
        """Write the example template file (always safe to overwrite)."""
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.build().to_dict(), fh, indent=2)
        return path

    def write_live_governance(self, state_dir: str, *,
                              overwrite: bool = False) -> Dict[str, Any]:
        """Write the disabled template into the live governance dir if absent.

        Never overwrites a customized governance file unless ``overwrite`` is set.
        """
        from ..live_birth.governance import GOVERNANCE_FILENAME

        gov_dir = os.path.join(state_dir, "governance")
        os.makedirs(gov_dir, exist_ok=True)
        path = os.path.join(gov_dir, GOVERNANCE_FILENAME)
        existed = os.path.isfile(path)
        if existed and not overwrite:
            return {"path": path, "written": False, "existed": True,
                    "note": "governance already present; not overwritten "
                            "(customized governance is preserved)"}
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.build().to_dict(), fh, indent=2)
        return {"path": path, "written": True, "existed": existed,
                "note": "wrote SAFE-OFF tester governance template (disabled + "
                        "unapproved); the tester must enable + approve by hand"}

    @staticmethod
    def load(state_dir: str) -> TesterLiveGovernanceTemplate:
        from ..live_birth.governance import GOVERNANCE_FILENAME

        path = os.path.join(state_dir, "governance", GOVERNANCE_FILENAME)
        if not os.path.isfile(path):
            return TesterLiveGovernanceTemplate(data={})
        try:
            with open(path, encoding="utf-8") as fh:
                return TesterLiveGovernanceTemplate(data=json.load(fh))
        except Exception:
            return TesterLiveGovernanceTemplate(data={})
