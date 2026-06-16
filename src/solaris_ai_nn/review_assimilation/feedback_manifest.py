"""Reviewer feedback manifest -- indexes local review feedback artifacts.

:class:`ReviewerFeedbackManifest` indexes the local feedback an external review
produced (objections, response-ledger entries, adversarial findings, audit-matrix
blockers, reproduction results, missing-artifact reports, sanitizer findings,
claim/theory objections, alternative explanations, operator notes). It indexes
local artifacts only, contacts no reviewer, uploads nothing, runs no command,
keeps missing reviewer material visible, preserves negative feedback, and can omit
or anonymize reviewer identity.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class FeedbackSourceType:
    REVIEWER_OBJECTION = "reviewer_objection"
    RESPONSE_LEDGER_ENTRY = "response_ledger_entry"
    ADVERSARIAL_REVIEW_FINDING = "adversarial_review_finding"
    AUDIT_MATRIX_BLOCKER = "audit_matrix_blocker"
    REPRODUCIBILITY_CHALLENGE_RESULT = "reproducibility_challenge_result"
    FAILED_REPRODUCTION = "failed_reproduction"
    SUCCESSFUL_REPRODUCTION = "successful_reproduction"
    MISSING_ARTIFACT_REPORT = "missing_artifact_report"
    SANITIZATION_FINDING = "sanitization_finding"
    CLAIM_OBJECTION = "claim_objection"
    THEORY_OBJECTION = "theory_objection"
    ALTERNATIVE_EXPLANATION = "alternative_explanation"
    OPERATOR_NOTE = "operator_note"
    UNKNOWN = "unknown"

    ALL = (REVIEWER_OBJECTION, RESPONSE_LEDGER_ENTRY,
           ADVERSARIAL_REVIEW_FINDING, AUDIT_MATRIX_BLOCKER,
           REPRODUCIBILITY_CHALLENGE_RESULT, FAILED_REPRODUCTION,
           SUCCESSFUL_REPRODUCTION, MISSING_ARTIFACT_REPORT,
           SANITIZATION_FINDING, CLAIM_OBJECTION, THEORY_OBJECTION,
           ALTERNATIVE_EXPLANATION, OPERATOR_NOTE, UNKNOWN)

    # Feedback that is intrinsically negative (must be preserved).
    NEGATIVE = (FAILED_REPRODUCTION, ADVERSARIAL_REVIEW_FINDING,
                AUDIT_MATRIX_BLOCKER, CLAIM_OBJECTION, THEORY_OBJECTION,
                ALTERNATIVE_EXPLANATION, SANITIZATION_FINDING)


class FeedbackArtifactStatus:
    PRESENT = "present"
    MISSING = "missing"
    ANONYMIZED = "anonymized"
    UNKNOWN = "unknown"

    ALL = (PRESENT, MISSING, ANONYMIZED, UNKNOWN)


@dataclass
class ReviewerFeedbackArtifact:
    """One indexed feedback artifact (local; reviewer identity optional)."""

    source_type: str
    ref: str = ""
    status: str = FeedbackArtifactStatus.PRESENT
    summary: str = ""
    reviewer_id: str = ""
    is_negative: bool = False

    def __post_init__(self) -> None:
        if self.source_type not in FeedbackSourceType.ALL:
            self.source_type = FeedbackSourceType.UNKNOWN
        if self.status not in FeedbackArtifactStatus.ALL:
            self.status = FeedbackArtifactStatus.UNKNOWN
        if self.source_type in FeedbackSourceType.NEGATIVE:
            self.is_negative = True

    def to_dict(self) -> Dict[str, Any]:
        return {"source_type": self.source_type, "ref": self.ref,
                "status": self.status, "summary": self.summary,
                "reviewer_id": self.reviewer_id, "is_negative": self.is_negative,
                "uploaded": False}


@dataclass
class ReviewerFeedbackManifest:
    """Indexes local reviewer feedback; missing material stays visible."""

    state_dir: str = ".solaris_ai_nn_review_assimilation"
    persist: bool = True
    anonymize: bool = True
    artifacts: List[ReviewerFeedbackArtifact] = field(default_factory=list,
                                                      init=False)
    created_ts: float = field(default_factory=time.time, init=False)

    @property
    def _manifest_path(self) -> str:
        return os.path.join(self.state_dir, "feedback_manifest.json")

    @property
    def _index_path(self) -> str:
        return os.path.join(self.state_dir, "feedback_artifact_index.json")

    def add(self, artifact: ReviewerFeedbackArtifact) -> ReviewerFeedbackArtifact:
        if self.anonymize:
            artifact.reviewer_id = ""
        self.artifacts.append(artifact)
        return artifact

    def add_missing(self, source_type: str, summary: str = "",
                    ) -> ReviewerFeedbackArtifact:
        return self.add(ReviewerFeedbackArtifact(
            source_type=source_type, status=FeedbackArtifactStatus.MISSING,
            summary=summary or "feedback artifact not present locally"))

    def present(self) -> List[ReviewerFeedbackArtifact]:
        return [a for a in self.artifacts
                if a.status == FeedbackArtifactStatus.PRESENT]

    def missing(self) -> List[ReviewerFeedbackArtifact]:
        return [a for a in self.artifacts
                if a.status == FeedbackArtifactStatus.MISSING]

    def negative(self) -> List[ReviewerFeedbackArtifact]:
        return [a for a in self.artifacts if a.is_negative]

    def index(self) -> Dict[str, Any]:
        return {
            "reviewer_feedback_artifact_count": len(self.artifacts),
            "present_feedback_count": len(self.present()),
            "missing_feedback_count": len(self.missing()),
            "negative_feedback_count": len(self.negative()),
            "anonymized": self.anonymize,
            "uploads": False,
        }

    def persist_manifest(self) -> Dict[str, str]:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._manifest_path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, default=str)
        with open(self._index_path, "w", encoding="utf-8") as fh:
            json.dump(self.index(), fh, indent=2, default=str)
        return {"manifest": self._manifest_path, "index": self._index_path}

    def to_dict(self) -> Dict[str, Any]:
        d = self.index()
        d["artifacts"] = [a.to_dict() for a in self.artifacts]
        d["note"] = ("indexes local reviewer feedback only; contacts no reviewer, "
                     "uploads nothing, runs no command; missing material stays "
                     "visible and negative feedback is preserved")
        return d
