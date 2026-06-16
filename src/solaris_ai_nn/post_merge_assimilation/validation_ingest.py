"""Post-merge validation ingest -- read operator-supplied validation results.

:class:`PostMergeValidationIngest` reads *local* validation-result artifacts the
operator supplies after running the post-merge validation plan by hand (full
test run, examples, safety invariants, ClaimGuard, short fixture demo, mini soak,
falsification replay, replication registration, operator review, resource
profile). It runs no validation itself; missing required artifacts can block
baseline validation; operator-provided validation is evidence, not proof.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ValidationArtifactType:
    FULL_TEST_RUN = "full_test_run"
    EXAMPLE_RUN = "example_run"
    SAFETY_INVARIANT_RUN = "safety_invariant_run"
    CLAIMGUARD_RUN = "claimguard_run"
    SHORT_FIXTURE_DEMO = "short_fixture_demo"
    MINI_SOAK = "mini_soak"
    FALSIFICATION_REPLAY = "falsification_replay"
    REPLICATION_REGISTRATION = "replication_registration"
    OPERATOR_REVIEW = "operator_review"
    RESOURCE_PROFILE = "resource_profile"
    UNKNOWN = "unknown"

    ALL = (FULL_TEST_RUN, EXAMPLE_RUN, SAFETY_INVARIANT_RUN, CLAIMGUARD_RUN,
           SHORT_FIXTURE_DEMO, MINI_SOAK, FALSIFICATION_REPLAY,
           REPLICATION_REGISTRATION, OPERATOR_REVIEW, RESOURCE_PROFILE, UNKNOWN)

    # Required validation artifacts (a missing one can block validation).
    REQUIRED = (FULL_TEST_RUN, SAFETY_INVARIANT_RUN, CLAIMGUARD_RUN)


@dataclass
class ValidationArtifact:
    """One ingested validation-result artifact (read-only evidence)."""

    artifact_type: str
    present: bool
    payload: Any = None
    passed: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"artifact_type": self.artifact_type, "present": self.present,
                "passed": self.passed, "has_payload": self.payload is not None}


@dataclass
class ValidationIngestResult:
    """The result of ingesting the supplied validation artifacts."""

    artifacts: List[ValidationArtifact] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)

    @property
    def present_count(self) -> int:
        return sum(1 for a in self.artifacts if a.present)

    @property
    def failed(self) -> List[str]:
        return [a.artifact_type for a in self.artifacts if a.passed is False]

    def get(self, artifact_type: str) -> Optional[ValidationArtifact]:
        return next((a for a in self.artifacts
                     if a.artifact_type == artifact_type), None)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "validation_artifact_count": self.present_count,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "missing_required": list(self.missing_required),
            "missing_validation_artifact_count": len(self.missing_required),
            "failed_validation": self.failed,
            "note": "ingest reads local artifacts only; no validation command "
                    "is executed; operator-provided validation is evidence, not "
                    "proof",
        }


def _passed(payload: Any) -> Optional[bool]:
    if not isinstance(payload, dict):
        return None
    if "passed" in payload:
        return bool(payload["passed"])
    if "safe" in payload:
        return bool(payload["safe"])
    if "failed" in payload:
        return int(payload.get("failed", 0) or 0) == 0
    if "ran" in payload:
        return bool(payload["ran"])
    return None


@dataclass
class PostMergeValidationIngest:
    """Ingests local validation results; never runs validation."""

    def ingest(self, validation_results: Optional[Dict[str, Any]] = None,
               ) -> ValidationIngestResult:
        results = validation_results or {}
        result = ValidationIngestResult()
        for atype in ValidationArtifactType.ALL:
            if atype == ValidationArtifactType.UNKNOWN:
                continue
            payload = results.get(atype)
            present = payload is not None
            result.artifacts.append(ValidationArtifact(
                artifact_type=atype, present=present, payload=payload,
                passed=_passed(payload) if present else None))
        result.missing_required = [
            a for a in ValidationArtifactType.REQUIRED
            if results.get(a) is None]
        return result
