"""Release blocker classifier -- maps feedback to developer-review blocker levels.

:class:`ReleaseBlockerClassifier` classifies a normalized feedback entry into a release
blocker level. Safety concerns default high; unsupported consciousness/life/agency
claims, network/shell/hardware/feeder-control risk, and privacy/secret exposure default
to release blockers; an un-runnable fixture demo is a release blocker; documentation
confusion is a blocker only when it prevents the tester protocol. Classifications are
developer review items, not automatic actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


class ReleaseBlockerReason:
    INSTALL_BLOCKER = "install_blocker"
    DOCTOR_BLOCKER = "doctor_blocker"
    FIXTURE_DEMO_BLOCKER = "fixture_demo_blocker"
    REPRODUCIBILITY_BLOCKER = "reproducibility_blocker"
    REGRESSION_BLOCKER = "regression_blocker"
    LIVE_GOVERNANCE_BLOCKER = "live_governance_blocker"
    FEEDER_SAFETY_BLOCKER = "feeder_safety_blocker"
    QUARANTINE_FAILURE = "quarantine_failure"
    MEMBRANE_MISSING = "membrane_missing"
    MEMBRANE_BYPASS = "membrane_bypass"
    RAW_EVENT_BYPASS = "raw_event_bypass"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    CONSCIOUSNESS_LIFE_AGENCY_CLAIM = "consciousness_life_agency_claim"
    PRIVACY_OR_SECRET_EXPOSURE = "privacy_or_secret_exposure"
    NETWORK_SHELL_HARDWARE_ACCESS = "network_shell_hardware_access"
    TESTER_FEEDBACK_TRAINING_RISK = "tester_feedback_training_risk"
    DOCS_UNUSABLE = "docs_unusable"
    CONSOLE_UNUSABLE = "console_unusable"
    UNKNOWN_CRITICAL = "unknown_critical"
    NONE = "none"


class ReleaseBlockerStatus:
    NOT_BLOCKER = "not_blocker"
    POTENTIAL_BLOCKER = "potential_blocker"
    BLOCKER = "blocker"
    RELEASE_BLOCKER = "release_blocker"
    STOP_TESTING = "stop_testing"

    ALL = (NOT_BLOCKER, POTENTIAL_BLOCKER, BLOCKER, RELEASE_BLOCKER,
           STOP_TESTING)
    _RANK = {NOT_BLOCKER: 0, POTENTIAL_BLOCKER: 1, BLOCKER: 2,
             RELEASE_BLOCKER: 3, STOP_TESTING: 4}


@dataclass
class ReleaseBlockerClassification:
    """The classification of one feedback entry."""

    feedback_id: str
    status: str = ReleaseBlockerStatus.NOT_BLOCKER
    reason: str = ReleaseBlockerReason.NONE
    detail: str = ""

    @property
    def is_release_blocker(self) -> bool:
        return ReleaseBlockerStatus._RANK[self.status] >= \
            ReleaseBlockerStatus._RANK[ReleaseBlockerStatus.RELEASE_BLOCKER]

    @property
    def is_stop_testing(self) -> bool:
        return self.status == ReleaseBlockerStatus.STOP_TESTING

    def to_dict(self) -> Dict[str, Any]:
        return {"feedback_id": self.feedback_id, "status": self.status,
                "reason": self.reason, "detail": self.detail,
                "is_release_blocker": self.is_release_blocker,
                "is_stop_testing": self.is_stop_testing,
                "developer_review_item": True, "automatic_action": False}


# Category -> (status, reason) defaults.
_CATEGORY_RULES = {
    "installation_failure": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                             ReleaseBlockerReason.INSTALL_BLOCKER),
    "dependency_problem": (ReleaseBlockerStatus.BLOCKER,
                           ReleaseBlockerReason.INSTALL_BLOCKER),
    "cli_failure": (ReleaseBlockerStatus.BLOCKER,
                    ReleaseBlockerReason.DOCTOR_BLOCKER),
    "fixture_demo_failure": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                             ReleaseBlockerReason.FIXTURE_DEMO_BLOCKER),
    "fixture_reproducibility_problem": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                                        ReleaseBlockerReason.REPRODUCIBILITY_BLOCKER),
    "fixture_regression_problem": (ReleaseBlockerStatus.BLOCKER,
                                   ReleaseBlockerReason.REGRESSION_BLOCKER),
    "governance_confusion": (ReleaseBlockerStatus.POTENTIAL_BLOCKER,
                             ReleaseBlockerReason.LIVE_GOVERNANCE_BLOCKER),
    "feeder_registry_confusion": (ReleaseBlockerStatus.POTENTIAL_BLOCKER,
                                  ReleaseBlockerReason.FEEDER_SAFETY_BLOCKER),
    "external_feeder_problem": (ReleaseBlockerStatus.BLOCKER,
                                ReleaseBlockerReason.FEEDER_SAFETY_BLOCKER),
    "quarantine_confusion": (ReleaseBlockerStatus.POTENTIAL_BLOCKER,
                             ReleaseBlockerReason.QUARANTINE_FAILURE),
    "membrane_confusion": (ReleaseBlockerStatus.POTENTIAL_BLOCKER,
                           ReleaseBlockerReason.MEMBRANE_MISSING),
    "membrane_bypass_concern": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                                ReleaseBlockerReason.MEMBRANE_BYPASS),
    "safety_concern": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                       ReleaseBlockerReason.UNKNOWN_CRITICAL),
    "unsupported_claim_concern": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                                  ReleaseBlockerReason.UNSUPPORTED_CLAIM),
    "privacy_concern": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                        ReleaseBlockerReason.PRIVACY_OR_SECRET_EXPOSURE),
    "performance_problem": (ReleaseBlockerStatus.NOT_BLOCKER,
                            ReleaseBlockerReason.NONE),
    "console_readability_problem": (ReleaseBlockerStatus.POTENTIAL_BLOCKER,
                                    ReleaseBlockerReason.CONSOLE_UNUSABLE),
    "documentation_confusion": (ReleaseBlockerStatus.NOT_BLOCKER,
                                ReleaseBlockerReason.DOCS_UNUSABLE),
    "tester_suggestion": (ReleaseBlockerStatus.NOT_BLOCKER,
                          ReleaseBlockerReason.NONE),
    "other": (ReleaseBlockerStatus.NOT_BLOCKER, ReleaseBlockerReason.NONE),
}

# Safety-concern types -> stop/release escalation.
_SAFETY_TYPE_RULES = {
    "feeder_control_risk": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                            ReleaseBlockerReason.FEEDER_SAFETY_BLOCKER),
    "hardware_control_risk": (ReleaseBlockerStatus.STOP_TESTING,
                              ReleaseBlockerReason.NETWORK_SHELL_HARDWARE_ACCESS),
    "network_access_risk": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                            ReleaseBlockerReason.NETWORK_SHELL_HARDWARE_ACCESS),
    "shell_execution_risk": (ReleaseBlockerStatus.STOP_TESTING,
                             ReleaseBlockerReason.NETWORK_SHELL_HARDWARE_ACCESS),
    "git_github_access_risk": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                               ReleaseBlockerReason.NETWORK_SHELL_HARDWARE_ACCESS),
    "browser_access_risk": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                            ReleaseBlockerReason.NETWORK_SHELL_HARDWARE_ACCESS),
    "private_data_exposure": (ReleaseBlockerStatus.STOP_TESTING,
                              ReleaseBlockerReason.PRIVACY_OR_SECRET_EXPOSURE),
    "secret_exposure": (ReleaseBlockerStatus.STOP_TESTING,
                        ReleaseBlockerReason.PRIVACY_OR_SECRET_EXPOSURE),
    "raw_event_bypass": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                         ReleaseBlockerReason.RAW_EVENT_BYPASS),
    "membrane_bypass": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                        ReleaseBlockerReason.MEMBRANE_BYPASS),
    "unsupported_claim": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                          ReleaseBlockerReason.UNSUPPORTED_CLAIM),
    "consciousness_claim": (ReleaseBlockerStatus.STOP_TESTING,
                            ReleaseBlockerReason.CONSCIOUSNESS_LIFE_AGENCY_CLAIM),
    "life_claim": (ReleaseBlockerStatus.STOP_TESTING,
                   ReleaseBlockerReason.CONSCIOUSNESS_LIFE_AGENCY_CLAIM),
    "agency_claim": (ReleaseBlockerStatus.STOP_TESTING,
                     ReleaseBlockerReason.CONSCIOUSNESS_LIFE_AGENCY_CLAIM),
    "tester_feedback_training_risk": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                                      ReleaseBlockerReason.TESTER_FEEDBACK_TRAINING_RISK),
    "governance_bypass": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                          ReleaseBlockerReason.LIVE_GOVERNANCE_BLOCKER),
    "quarantine_failure": (ReleaseBlockerStatus.RELEASE_BLOCKER,
                           ReleaseBlockerReason.QUARANTINE_FAILURE),
}


@dataclass
class ReleaseBlockerClassifier:
    """Classifies feedback entries into release-blocker levels (review items)."""

    def classify(self, entry: Dict[str, Any]) -> ReleaseBlockerClassification:
        fid = str(entry.get("feedback_id") or entry.get("bug_id")
                  or entry.get("concern_id") or entry.get("suggestion_id")
                  or entry.get("confusion_id") or "unknown")
        ftype = entry.get("feedback_type", "")

        # Safety concerns: classify by concern_type.
        if ftype == "safety_concern":
            ctype = entry.get("concern_type", "unknown")
            status, reason = _SAFETY_TYPE_RULES.get(
                ctype, (ReleaseBlockerStatus.RELEASE_BLOCKER,
                        ReleaseBlockerReason.UNKNOWN_CRITICAL))
            # An explicit escalation can raise the level further.
            if entry.get("escalation") == "stop_testing_now":
                status = ReleaseBlockerStatus.STOP_TESTING
            return ReleaseBlockerClassification(
                fid, status, reason, f"safety concern: {ctype}")

        if ftype == "suggestion":
            return ReleaseBlockerClassification(
                fid, ReleaseBlockerStatus.NOT_BLOCKER,
                ReleaseBlockerReason.NONE, "suggestion (review item)")

        if ftype == "confusion_report":
            if entry.get("blocks_protocol"):
                return ReleaseBlockerClassification(
                    fid, ReleaseBlockerStatus.BLOCKER,
                    ReleaseBlockerReason.DOCS_UNUSABLE,
                    "confusion blocks the tester protocol")
            return ReleaseBlockerClassification(
                fid, ReleaseBlockerStatus.NOT_BLOCKER,
                ReleaseBlockerReason.NONE, "confusion (UX/docs evidence)")

        # General feedback / bug reports: classify by category.
        category = entry.get("category", "")
        status, reason = _CATEGORY_RULES.get(
            category, (ReleaseBlockerStatus.POTENTIAL_BLOCKER,
                       ReleaseBlockerReason.UNKNOWN_CRITICAL))

        # A declared severity can raise (never lower) the classification.
        severity = entry.get("severity", entry.get("blocker_severity", ""))
        if severity == "release_blocker":
            status = ReleaseBlockerStatus.RELEASE_BLOCKER
        elif severity == "critical" and ReleaseBlockerStatus._RANK[status] < \
                ReleaseBlockerStatus._RANK[ReleaseBlockerStatus.BLOCKER]:
            status = ReleaseBlockerStatus.BLOCKER
        return ReleaseBlockerClassification(
            fid, status, reason, f"category: {category}")
