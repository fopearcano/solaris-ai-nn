"""Reproduction outcomes -- a reviewer's reproduction result is evidence.

:class:`ReviewerReproductionOutcomeIngestor` records the outcome of a reviewer
running a reproducibility challenge. Failed and partial reproduction are evidence;
successful reproduction does not prove consciousness/life/agency; and a missing
artifact is, by default, a project limitation rather than reviewer failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ReproductionOutcomeStatus:
    REPRODUCED = "reproduced"
    PARTIALLY_REPRODUCED = "partially_reproduced"
    NOT_REPRODUCED = "not_reproduced"
    BLOCKED_BY_MISSING_ARTIFACT = "blocked_by_missing_artifact"
    BLOCKED_BY_ENVIRONMENT = "blocked_by_environment"
    BLOCKED_BY_COMMAND_FAILURE = "blocked_by_command_failure"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    INCONCLUSIVE = "inconclusive"
    UNKNOWN = "unknown"

    ALL = (REPRODUCED, PARTIALLY_REPRODUCED, NOT_REPRODUCED,
           BLOCKED_BY_MISSING_ARTIFACT, BLOCKED_BY_ENVIRONMENT,
           BLOCKED_BY_COMMAND_FAILURE, BLOCKED_BY_SAFETY, INCONCLUSIVE, UNKNOWN)

    SUCCESS = (REPRODUCED, PARTIALLY_REPRODUCED)
    FAILURE = (NOT_REPRODUCED,)
    # A missing artifact is a project limitation, not reviewer failure.
    PROJECT_LIMITATION = (BLOCKED_BY_MISSING_ARTIFACT,)


class ReproductionFailureReason:
    MISSING_FIXTURE = "missing_fixture"
    MISSING_REPORT = "missing_report"
    DEPENDENCY_MISMATCH = "dependency_mismatch"
    COMMAND_UNDOCUMENTED = "command_undocumented"
    EXPECTED_OUTPUT_MISMATCH = "expected_output_mismatch"
    CLAIMGUARD_FAILURE = "claimguard_failure"
    SAFETY_INVARIANT_FAILURE = "safety_invariant_failure"
    TEST_FAILURE = "test_failure"
    METRIC_MISMATCH = "metric_mismatch"
    ARTIFACT_CORRUPTION = "artifact_corruption"
    REVIEWER_ENVIRONMENT_MISMATCH = "reviewer_environment_mismatch"
    UNKNOWN = "unknown"

    ALL = (MISSING_FIXTURE, MISSING_REPORT, DEPENDENCY_MISMATCH,
           COMMAND_UNDOCUMENTED, EXPECTED_OUTPUT_MISMATCH, CLAIMGUARD_FAILURE,
           SAFETY_INVARIANT_FAILURE, TEST_FAILURE, METRIC_MISMATCH,
           ARTIFACT_CORRUPTION, REVIEWER_ENVIRONMENT_MISMATCH, UNKNOWN)

    # Reasons that are the project's responsibility (not the reviewer's).
    PROJECT_SIDE = (MISSING_FIXTURE, MISSING_REPORT, COMMAND_UNDOCUMENTED,
                    CLAIMGUARD_FAILURE, SAFETY_INVARIANT_FAILURE,
                    ARTIFACT_CORRUPTION)


@dataclass
class ReviewerReproductionOutcome:
    """One reviewer reproduction outcome (a reproduction result is evidence)."""

    challenge_type: str
    status: str = ReproductionOutcomeStatus.UNKNOWN
    failure_reason: str = ""
    claim_refs: List[str] = field(default_factory=list)
    detail: str = ""

    def __post_init__(self) -> None:
        if self.status not in ReproductionOutcomeStatus.ALL:
            self.status = ReproductionOutcomeStatus.UNKNOWN
        if self.failure_reason and \
                self.failure_reason not in ReproductionFailureReason.ALL:
            self.failure_reason = ReproductionFailureReason.UNKNOWN

    @property
    def is_success(self) -> bool:
        return self.status in ReproductionOutcomeStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        return self.status in ReproductionOutcomeStatus.FAILURE

    @property
    def is_project_limitation(self) -> bool:
        return (self.status in ReproductionOutcomeStatus.PROJECT_LIMITATION
                or self.failure_reason in ReproductionFailureReason.PROJECT_SIDE)

    def to_dict(self) -> Dict[str, Any]:
        return {"challenge_type": self.challenge_type, "status": self.status,
                "failure_reason": self.failure_reason,
                "claim_refs": list(self.claim_refs), "detail": self.detail,
                "is_success": self.is_success, "is_failure": self.is_failure,
                "is_project_limitation": self.is_project_limitation,
                "is_evidence": True,
                "proves_consciousness": False}


@dataclass
class ReviewerReproductionOutcomeIngestor:
    """Ingests reviewer reproduction outcomes from local records."""

    def ingest(self, records: List[Dict[str, Any]],
               ) -> List[ReviewerReproductionOutcome]:
        out: List[ReviewerReproductionOutcome] = []
        for r in records or []:
            out.append(ReviewerReproductionOutcome(
                challenge_type=str(r.get("challenge_type", "unknown")),
                status=str(r.get("status",
                                 ReproductionOutcomeStatus.UNKNOWN)),
                failure_reason=str(r.get("failure_reason", "")),
                claim_refs=list(r.get("claim_refs", [])),
                detail=str(r.get("detail", ""))))
        return out

    @staticmethod
    def summary(outcomes: List[ReviewerReproductionOutcome]) -> Dict[str, Any]:
        return {
            "reproduction_outcome_count": len(outcomes),
            "reproduction_success_count": sum(1 for o in outcomes
                                              if o.is_success),
            "reproduction_failure_count": sum(1 for o in outcomes
                                              if o.is_failure),
            "project_limitation_count": sum(1 for o in outcomes
                                            if o.is_project_limitation),
            "outcomes": [o.to_dict() for o in outcomes],
            "note": "failed and partial reproduction are evidence; successful "
                    "reproduction does not prove consciousness/life/agency; a "
                    "missing artifact is a project limitation, not reviewer "
                    "failure by default",
        }
