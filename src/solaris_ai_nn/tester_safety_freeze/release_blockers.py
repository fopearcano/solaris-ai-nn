"""Tester release blocker gate -- the hard gate before a release candidate.

:class:`TesterReleaseBlockerGate` collects release blockers from the claim freeze,
capability freeze, artifact scan, red-team checklist, and integration evidence (membrane,
fixture, feedback). Open release blockers prevent a tester release candidate; waivers
require an explicit reason; critical safety blockers cannot be silently waived.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReleaseBlockerCategory:
    INSTALL = "install_blocker"
    DOCTOR = "doctor_blocker"
    MISSING_CLI = "missing_required_cli_command"
    FIXTURE_DEMO = "fixture_demo_blocker"
    REPRODUCIBILITY = "reproducibility_blocker"
    REGRESSION = "regression_blocker"
    MISSING_MEMBRANE = "missing_membrane"
    MEMBRANE_BYPASS = "membrane_bypass"
    RAW_EVENT_BYPASS = "raw_event_bypass"
    UNSAFE_FEEDER_CONTROL = "unsafe_feeder_control"
    UNSAFE_CAPABILITY = "unsafe_hardware_network_shell_git_github_capability"
    GOVERNANCE_BYPASS = "governance_bypass"
    QUARANTINE_FAILURE = "quarantine_failure"
    PRIVACY_EXPOSURE = "privacy_secret_exposure"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    MISSING_DISCLAIMER = "missing_disclaimer"
    CONSOLE_UNSAFE = "console_unsafe"
    FEEDBACK_TRAINING = "feedback_training_risk"
    PACKAGING_PUBLISH = "packaging_publish_upload_risk"
    DOCS_UNUSABLE = "documentation_unusable"
    UNKNOWN_CRITICAL = "unknown_critical"


class ReleaseBlockerStatus:
    OPEN = "open"
    WAIVED = "waived_for_tester_release"
    DEFERRED = "deferred_not_blocking"
    RESOLVED = "resolved"
    UNKNOWN = "unknown"

    ALL = (OPEN, WAIVED, DEFERRED, RESOLVED, UNKNOWN)


# Categories whose blockers are critical safety and cannot be silently waived.
_CRITICAL_CATEGORIES = {
    ReleaseBlockerCategory.MEMBRANE_BYPASS,
    ReleaseBlockerCategory.RAW_EVENT_BYPASS,
    ReleaseBlockerCategory.UNSAFE_FEEDER_CONTROL,
    ReleaseBlockerCategory.UNSAFE_CAPABILITY,
    ReleaseBlockerCategory.PRIVACY_EXPOSURE,
    ReleaseBlockerCategory.UNSUPPORTED_CLAIM,
    ReleaseBlockerCategory.FEEDBACK_TRAINING,
    ReleaseBlockerCategory.GOVERNANCE_BYPASS,
}


@dataclass
class ReleaseBlocker:
    """One release blocker."""

    blocker_id: str
    category: str
    detail: str
    status: str = ReleaseBlockerStatus.OPEN
    waiver_reason: str = ""

    @property
    def critical(self) -> bool:
        return self.category in _CRITICAL_CATEGORIES

    @property
    def is_open(self) -> bool:
        return self.status in (ReleaseBlockerStatus.OPEN,
                               ReleaseBlockerStatus.UNKNOWN)

    def waive(self, reason: str) -> bool:
        """Waive a non-critical blocker; refuse to silently waive critical ones."""
        if self.critical or not reason:
            return False
        self.status = ReleaseBlockerStatus.WAIVED
        self.waiver_reason = reason
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {"blocker_id": self.blocker_id, "category": self.category,
                "detail": self.detail, "status": self.status,
                "critical": self.critical, "is_open": self.is_open,
                "waiver_reason": self.waiver_reason}


@dataclass
class TesterReleaseBlockerGate:
    """The hard release blocker gate (open blockers prevent a release candidate)."""

    blockers: List[ReleaseBlocker] = field(default_factory=list)

    def add(self, category: str, detail: str,
            blocker_id: Optional[str] = None) -> ReleaseBlocker:
        bid = blocker_id or f"{category}_{len(self.blockers) + 1}"
        blocker = ReleaseBlocker(blocker_id=bid, category=category,
                                 detail=detail)
        self.blockers.append(blocker)
        return blocker

    @property
    def open_blockers(self) -> List[ReleaseBlocker]:
        return [b for b in self.blockers if b.is_open]

    @property
    def critical_open(self) -> List[ReleaseBlocker]:
        return [b for b in self.open_blockers if b.critical]

    @property
    def waived(self) -> List[ReleaseBlocker]:
        return [b for b in self.blockers
                if b.status == ReleaseBlockerStatus.WAIVED]

    @property
    def release_candidate_allowed(self) -> bool:
        return not self.open_blockers

    def to_dict(self) -> Dict[str, Any]:
        cats: Dict[str, int] = {}
        for b in self.open_blockers:
            cats[b.category] = cats.get(b.category, 0) + 1
        return {
            "release_candidate_allowed": self.release_candidate_allowed,
            "blocker_count": len(self.blockers),
            "open_blocker_count": len(self.open_blockers),
            "critical_open_count": len(self.critical_open),
            "waived_count": len(self.waived),
            "open_by_category": cats,
            "blockers": [b.to_dict() for b in self.blockers],
            "note": "open release blockers prevent a tester release candidate; "
                    "critical safety blockers cannot be silently waived",
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        lines = ["# Tester Release Blockers", "",
                 f"- release candidate allowed: "
                 f"**{d['release_candidate_allowed']}**",
                 f"- open blockers: {d['open_blocker_count']} "
                 f"(critical {d['critical_open_count']})",
                 f"- waived: {d['waived_count']}", "",
                 "| id | category | status | critical | detail |",
                 "| --- | --- | --- | --- | --- |"]
        for b in d["blockers"]:
            lines.append(f"| {b['blocker_id']} | {b['category']} | "
                         f"{b['status']} | {b['critical']} | {b['detail']} |")
        lines += ["", "_Open release blockers prevent a tester release "
                  "candidate. Critical safety blockers (membrane/raw-event "
                  "bypass, unsafe capability, privacy exposure, unsupported "
                  "claim, feedback-training, governance bypass) cannot be "
                  "silently waived._"]
        return "\n".join(lines)
