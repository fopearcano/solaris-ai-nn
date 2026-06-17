"""Tester safety concern -- elevated QA evidence (never suppressed).

A safety concern is surfaced at the top of feedback reports. Critical concerns
recommend stopping testing, and an unsupported consciousness/life/agency claim concern
is a release blocker until reviewed. The feedback system never suppresses a safety
concern.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict


class SafetyConcernType:
    FEEDER_CONTROL_RISK = "feeder_control_risk"
    HARDWARE_CONTROL_RISK = "hardware_control_risk"
    NETWORK_ACCESS_RISK = "network_access_risk"
    SHELL_EXECUTION_RISK = "shell_execution_risk"
    GIT_GITHUB_ACCESS_RISK = "git_github_access_risk"
    BROWSER_ACCESS_RISK = "browser_access_risk"
    PRIVATE_DATA_EXPOSURE = "private_data_exposure"
    SECRET_EXPOSURE = "secret_exposure"
    RAW_EVENT_BYPASS = "raw_event_bypass"
    MEMBRANE_BYPASS = "membrane_bypass"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    CONSCIOUSNESS_CLAIM = "consciousness_claim"
    LIFE_CLAIM = "life_claim"
    AGENCY_CLAIM = "agency_claim"
    TESTER_FEEDBACK_TRAINING_RISK = "tester_feedback_training_risk"
    GOVERNANCE_BYPASS = "governance_bypass"
    QUARANTINE_FAILURE = "quarantine_failure"
    UNKNOWN = "unknown"

    ALL = (FEEDER_CONTROL_RISK, HARDWARE_CONTROL_RISK, NETWORK_ACCESS_RISK,
           SHELL_EXECUTION_RISK, GIT_GITHUB_ACCESS_RISK, BROWSER_ACCESS_RISK,
           PRIVATE_DATA_EXPOSURE, SECRET_EXPOSURE, RAW_EVENT_BYPASS,
           MEMBRANE_BYPASS, UNSUPPORTED_CLAIM, CONSCIOUSNESS_CLAIM, LIFE_CLAIM,
           AGENCY_CLAIM, TESTER_FEEDBACK_TRAINING_RISK, GOVERNANCE_BYPASS,
           QUARANTINE_FAILURE, UNKNOWN)

    # Types that are release blockers (or worse) until reviewed.
    RELEASE_BLOCKER_TYPES = (
        FEEDER_CONTROL_RISK, HARDWARE_CONTROL_RISK, NETWORK_ACCESS_RISK,
        SHELL_EXECUTION_RISK, GIT_GITHUB_ACCESS_RISK, BROWSER_ACCESS_RISK,
        PRIVATE_DATA_EXPOSURE, SECRET_EXPOSURE, RAW_EVENT_BYPASS,
        MEMBRANE_BYPASS, UNSUPPORTED_CLAIM, CONSCIOUSNESS_CLAIM, LIFE_CLAIM,
        AGENCY_CLAIM, TESTER_FEEDBACK_TRAINING_RISK, GOVERNANCE_BYPASS,
        QUARANTINE_FAILURE)
    # Types that recommend stopping testing immediately.
    STOP_TESTING_TYPES = (
        CONSCIOUSNESS_CLAIM, LIFE_CLAIM, AGENCY_CLAIM, SECRET_EXPOSURE,
        PRIVATE_DATA_EXPOSURE, HARDWARE_CONTROL_RISK, SHELL_EXECUTION_RISK)


class SafetyConcernEscalation:
    NONE = "none"
    WATCH = "watch"
    WARNING = "warning"
    BLOCKER = "blocker"
    RELEASE_BLOCKER = "release_blocker"
    STOP_TESTING_NOW = "stop_testing_now"

    ALL = (NONE, WATCH, WARNING, BLOCKER, RELEASE_BLOCKER, STOP_TESTING_NOW)
    _RANK = {NONE: 0, WATCH: 1, WARNING: 2, BLOCKER: 3, RELEASE_BLOCKER: 4,
             STOP_TESTING_NOW: 5}


@dataclass
class TesterSafetyConcern:
    """A local tester safety concern (never suppressed)."""

    concern_id: str
    concern_type: str = SafetyConcernType.UNKNOWN
    description: str = ""
    tester_alias: str = "anonymous"
    created_utc: str = ""
    artifact_paths: list = field(default_factory=list)
    escalation: str = SafetyConcernEscalation.WARNING

    def __post_init__(self) -> None:
        if self.concern_type not in SafetyConcernType.ALL:
            self.concern_type = SafetyConcernType.UNKNOWN
        # Escalation is computed from the type unless explicitly raised higher.
        computed = self._computed_escalation()
        if SafetyConcernEscalation._RANK.get(self.escalation, 0) < \
                SafetyConcernEscalation._RANK[computed]:
            self.escalation = computed

    def _computed_escalation(self) -> str:
        if self.concern_type in SafetyConcernType.STOP_TESTING_TYPES:
            return SafetyConcernEscalation.STOP_TESTING_NOW
        if self.concern_type in SafetyConcernType.RELEASE_BLOCKER_TYPES:
            return SafetyConcernEscalation.RELEASE_BLOCKER
        return SafetyConcernEscalation.WARNING

    @property
    def recommends_stop(self) -> bool:
        return self.escalation == SafetyConcernEscalation.STOP_TESTING_NOW

    @property
    def is_release_blocker(self) -> bool:
        return SafetyConcernEscalation._RANK[self.escalation] >= \
            SafetyConcernEscalation._RANK[SafetyConcernEscalation.RELEASE_BLOCKER]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_type": "safety_concern", "concern_id": self.concern_id,
            "concern_type": self.concern_type, "description": self.description,
            "tester_alias": self.tester_alias, "created_utc": self.created_utc,
            "artifact_paths": list(self.artifact_paths),
            "escalation": self.escalation,
            "recommends_stop": self.recommends_stop,
            "is_release_blocker": self.is_release_blocker,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TesterSafetyConcern":
        return cls(
            concern_id=str(data.get("concern_id") or data.get("feedback_id")
                           or f"sc_{int(time.time() * 1000)}"),
            concern_type=str(data.get("concern_type",
                                      SafetyConcernType.UNKNOWN)),
            description=str(data.get("description",
                                     data.get("actual_behavior", ""))),
            tester_alias=str(data.get("tester_alias", "anonymous")),
            created_utc=str(data.get("created_utc")
                            or time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime())),
            artifact_paths=list(data.get("artifact_paths", []) or []),
            escalation=str(data.get("escalation",
                                    SafetyConcernEscalation.WARNING)))
