"""Post-merge manifest -- the operator's local record of an external merge.

:class:`PostMergeManifest` records that a human merged or accepted a change
*outside* Solaris, plus the local artifacts to assimilate. It is local evidence
only: it never calls GitHub to verify a PR and never runs Git to verify a commit.
A missing commit hash is allowed but recorded as uncertainty, and an operator
note can clarify but never overrides a safety failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class MergeSourceType:
    HUMAN_CONFIRMED_MERGE = "human_confirmed_merge"
    MANUAL_CODE_UPDATE = "manual_code_update"
    EXTERNAL_PR_MERGE = "external_pr_merge"
    LOCAL_BRANCH_ACCEPTANCE = "local_branch_acceptance"
    RELEASE_CANDIDATE_ACCEPTANCE = "release_candidate_acceptance"
    UNKNOWN = "unknown"

    ALL = (HUMAN_CONFIRMED_MERGE, MANUAL_CODE_UPDATE, EXTERNAL_PR_MERGE,
           LOCAL_BRANCH_ACCEPTANCE, RELEASE_CANDIDATE_ACCEPTANCE, UNKNOWN)


@dataclass
class MergeConfirmation:
    """The operator's confirmation that a human accepted the change."""

    confirmed_by_operator: bool = False
    statement: str = ""
    merged_timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"confirmed_by_operator": self.confirmed_by_operator,
                "statement": self.statement,
                "merged_timestamp": self.merged_timestamp}


@dataclass
class MergeArtifact:
    """One local artifact referenced by the merge manifest."""

    artifact_id: str
    path: str = ""
    present: bool = False
    payload: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {"artifact_id": self.artifact_id, "path": self.path,
                "present": self.present, "has_payload": self.payload is not None}


@dataclass
class PostMergeManifest:
    """Local record of an external human merge + the artifacts to assimilate."""

    merge_id: str = "merge"
    confirmation: MergeConfirmation = field(default_factory=MergeConfirmation)
    source_experiment_id: str = ""
    source_branch_spec_id: str = ""
    source_implementation_intake_report: str = ""
    merge_source_type: str = MergeSourceType.UNKNOWN
    external_commit_hash: Optional[str] = None
    external_pr_number: Optional[str] = None
    merged_timestamp: Optional[str] = None
    target_baseline_id: str = ""
    artifacts: Dict[str, MergeArtifact] = field(default_factory=dict)
    validation_result_paths: Dict[str, str] = field(default_factory=dict)
    operator_notes: str = ""
    limitations: List[str] = field(default_factory=list)
    uncertainty: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.merge_source_type not in MergeSourceType.ALL:
            self.merge_source_type = MergeSourceType.UNKNOWN
        if not self.external_commit_hash:
            self.uncertainty.append("missing external commit hash (allowed)")
        if not self.external_pr_number:
            self.uncertainty.append("missing external PR number (allowed)")
        if not self.confirmation.confirmed_by_operator:
            self.uncertainty.append("merge not operator-confirmed")

    def add_artifact(self, artifact_id: str, *, path: str = "",
                     payload: Any = None) -> MergeArtifact:
        art = MergeArtifact(artifact_id=artifact_id, path=path, payload=payload,
                            present=payload is not None or bool(path))
        self.artifacts[artifact_id] = art
        return art

    @property
    def operator_confirmed(self) -> bool:
        return self.confirmation.confirmed_by_operator

    def to_dict(self) -> Dict[str, Any]:
        return {
            "merge_id": self.merge_id,
            "confirmation": self.confirmation.to_dict(),
            "operator_confirmed": self.operator_confirmed,
            "source_experiment_id": self.source_experiment_id,
            "source_branch_spec_id": self.source_branch_spec_id,
            "source_implementation_intake_report":
                self.source_implementation_intake_report,
            "merge_source_type": self.merge_source_type,
            "external_commit_hash": self.external_commit_hash,
            "external_pr_number": self.external_pr_number,
            "merged_timestamp": self.merged_timestamp,
            "target_baseline_id": self.target_baseline_id,
            "artifacts": {aid: a.to_dict() for aid, a in self.artifacts.items()},
            "validation_result_paths": dict(self.validation_result_paths),
            "operator_notes": self.operator_notes,
            "limitations": list(self.limitations),
            "uncertainty": list(self.uncertainty),
            "note": ("local evidence only; no GitHub call verifies the PR and "
                     "no Git command verifies the commit; an operator note "
                     "never overrides a safety failure"),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PostMergeManifest":
        data = dict(data or {})
        conf = data.pop("confirmation", {}) or {}
        manifest = cls(
            merge_id=data.get("merge_id", "merge"),
            confirmation=MergeConfirmation(
                confirmed_by_operator=bool(conf.get("confirmed_by_operator")),
                statement=conf.get("statement", ""),
                merged_timestamp=conf.get("merged_timestamp")),
            source_experiment_id=data.get("source_experiment_id", ""),
            source_branch_spec_id=data.get("source_branch_spec_id", ""),
            source_implementation_intake_report=data.get(
                "source_implementation_intake_report", ""),
            merge_source_type=data.get("merge_source_type",
                                       MergeSourceType.UNKNOWN),
            external_commit_hash=data.get("external_commit_hash"),
            external_pr_number=data.get("external_pr_number"),
            merged_timestamp=data.get("merged_timestamp"),
            target_baseline_id=data.get("target_baseline_id", ""),
            validation_result_paths=dict(
                data.get("validation_result_paths", {})),
            operator_notes=data.get("operator_notes", ""),
            limitations=list(data.get("limitations", [])))
        for aid, payload in (data.get("artifacts", {}) or {}).items():
            manifest.add_artifact(aid, payload=payload)
        return manifest
