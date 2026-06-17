"""Tester confusion report -- documentation/UX evidence (not a teaching signal).

Confusion reports are documentation/UX evidence. They are not teaching signals and do
not modify any system concept.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict


class ConfusionArea:
    INSTALL = "install"
    COMMAND_NAMING = "command_naming"
    STATE_DIRECTORIES = "state_directories"
    FIXTURE_VS_LIVE = "fixture_vs_live_distinction"
    GOVERNANCE = "governance"
    FEEDER_REGISTRY = "feeder_registry"
    MEMBRANE_CONCEPT = "membrane_concept"
    SENSORY_IMPRESSIONS = "sensory_impressions"
    QUARANTINE = "quarantine"
    SOURCE_PRESSURE = "source_pressure"
    OBSERVATION_REPORTS = "observation_reports"
    CONSOLE_DASHBOARD = "console_dashboard"
    ARTIFACT_BUNDLE = "artifact_bundle"
    SCIENTIFIC_CLAIMS = "scientific_claims"
    NEXT_ACTIONS = "next_actions"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"

    ALL = (INSTALL, COMMAND_NAMING, STATE_DIRECTORIES, FIXTURE_VS_LIVE,
           GOVERNANCE, FEEDER_REGISTRY, MEMBRANE_CONCEPT, SENSORY_IMPRESSIONS,
           QUARANTINE, SOURCE_PRESSURE, OBSERVATION_REPORTS, CONSOLE_DASHBOARD,
           ARTIFACT_BUNDLE, SCIENTIFIC_CLAIMS, NEXT_ACTIONS, DOCUMENTATION,
           UNKNOWN)


class ConfusionSeverity:
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    BLOCKS_PROTOCOL = "blocks_protocol"
    UNKNOWN = "unknown"

    ALL = (INFO, MINOR, MAJOR, BLOCKS_PROTOCOL, UNKNOWN)


@dataclass
class TesterConfusionReport:
    """A local confusion report (documentation/UX evidence; not teaching)."""

    confusion_id: str
    area: str = ConfusionArea.UNKNOWN
    severity: str = ConfusionSeverity.MINOR
    description: str = ""
    tester_alias: str = "anonymous"
    created_utc: str = ""
    artifact_paths: list = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.area not in ConfusionArea.ALL:
            self.area = ConfusionArea.UNKNOWN
        if self.severity not in ConfusionSeverity.ALL:
            self.severity = ConfusionSeverity.UNKNOWN

    @property
    def blocks_protocol(self) -> bool:
        return self.severity == ConfusionSeverity.BLOCKS_PROTOCOL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_type": "confusion_report", "confusion_id": self.confusion_id,
            "area": self.area, "severity": self.severity,
            "description": self.description, "tester_alias": self.tester_alias,
            "created_utc": self.created_utc,
            "artifact_paths": list(self.artifact_paths),
            "blocks_protocol": self.blocks_protocol,
            "is_teaching_signal": False, "modifies_system_concepts": False,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TesterConfusionReport":
        return cls(
            confusion_id=str(data.get("confusion_id") or data.get("feedback_id")
                             or f"cf_{int(time.time() * 1000)}"),
            area=str(data.get("area", data.get("stage_affected",
                                                ConfusionArea.UNKNOWN))),
            severity=str(data.get("severity", ConfusionSeverity.MINOR)),
            description=str(data.get("description",
                                     data.get("actual_behavior", ""))),
            tester_alias=str(data.get("tester_alias", "anonymous")),
            created_utc=str(data.get("created_utc")
                            or time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime())),
            artifact_paths=list(data.get("artifact_paths", []) or []))
