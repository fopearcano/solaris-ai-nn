"""Tester suggestion report -- review items only (not ground truth, never auto-applied).

Suggestions are not ground truth, do not modify runtime behaviour, and never trigger
implementation automatically. Each suggestion has a developer-controlled disposition.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict


class SuggestionType:
    DOCUMENTATION = "documentation"
    CLI_USABILITY = "cli_usability"
    CONSOLE_READABILITY = "console_readability"
    REPORT_CLARITY = "report_clarity"
    FIXTURE_COVERAGE = "fixture_coverage"
    LIVE_TESTER_WORKFLOW = "live_tester_workflow"
    SAFETY_WORDING = "safety_wording"
    PACKAGING = "packaging"
    PERFORMANCE = "performance"
    ARCHITECTURE = "architecture"
    FUTURE_FEATURE = "future_feature"
    OTHER = "other"

    ALL = (DOCUMENTATION, CLI_USABILITY, CONSOLE_READABILITY, REPORT_CLARITY,
           FIXTURE_COVERAGE, LIVE_TESTER_WORKFLOW, SAFETY_WORDING, PACKAGING,
           PERFORMANCE, ARCHITECTURE, FUTURE_FEATURE, OTHER)


class SuggestionDisposition:
    UNREVIEWED = "unreviewed"
    ACCEPTED_FOR_REVIEW = "accepted_for_review"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    NEEDS_CLARIFICATION = "needs_clarification"

    ALL = (UNREVIEWED, ACCEPTED_FOR_REVIEW, DEFERRED, REJECTED, DUPLICATE,
           NEEDS_CLARIFICATION)


@dataclass
class TesterSuggestionReport:
    """A local tester suggestion (review item only; never auto-applied)."""

    suggestion_id: str
    suggestion_type: str = SuggestionType.OTHER
    description: str = ""
    tester_alias: str = "anonymous"
    created_utc: str = ""
    disposition: str = SuggestionDisposition.UNREVIEWED

    def __post_init__(self) -> None:
        if self.suggestion_type not in SuggestionType.ALL:
            self.suggestion_type = SuggestionType.OTHER
        if self.disposition not in SuggestionDisposition.ALL:
            self.disposition = SuggestionDisposition.UNREVIEWED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_type": "suggestion", "suggestion_id": self.suggestion_id,
            "suggestion_type": self.suggestion_type,
            "description": self.description, "tester_alias": self.tester_alias,
            "created_utc": self.created_utc, "disposition": self.disposition,
            "is_ground_truth": False, "modifies_runtime_behavior": False,
            "triggers_implementation": False,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TesterSuggestionReport":
        return cls(
            suggestion_id=str(data.get("suggestion_id")
                              or data.get("feedback_id")
                              or f"sg_{int(time.time() * 1000)}"),
            suggestion_type=str(data.get("suggestion_type",
                                         SuggestionType.OTHER)),
            description=str(data.get("description",
                                     data.get("actual_behavior", ""))),
            tester_alias=str(data.get("tester_alias", "anonymous")),
            created_utc=str(data.get("created_utc")
                            or time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime())),
            disposition=str(data.get("disposition",
                                     SuggestionDisposition.UNREVIEWED)))
