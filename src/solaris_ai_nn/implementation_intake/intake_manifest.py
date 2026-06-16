"""Implementation-intake manifest -- declare the local artifacts to audit.

:class:`ImplementationIntakeManifest` declares the artifacts an external
implementation must supply for audit: the compiler's reference artifacts
(implementation prompt, branch spec, test matrix, safety gates, operator review
packet, rollback/validation plan) plus the implementation's own evidence
(summary, diff/patch, changed file list, test/example/ClaimGuard/safety-invariant
results, lint/typecheck, PR metadata). It reads *local* artifacts only and never
calls GitHub. Missing required artifacts block readiness; missing optional ones
warn; and an operator note may clarify but never overrides a safety failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ImplementationArtifactStatus:
    PRESENT = "present"
    PROVIDED = "provided"
    MISSING_WARNING = "missing_warning"
    MISSING_BLOCKER = "missing_blocker"
    CORRUPT = "corrupt"
    EMPTY = "empty"

    ALL = (PRESENT, PROVIDED, MISSING_WARNING, MISSING_BLOCKER, CORRUPT, EMPTY)


# Each artifact: (id, is_required). Required-missing => blocker, else warning.
_ARTIFACT_SPEC = (
    ("implementation_prompt", False),
    ("branch_spec", False),
    ("test_matrix", False),
    ("safety_gates", True),
    ("operator_review_packet", False),
    ("rollback_plan", False),
    ("validation_plan", False),
    ("implementation_summary", True),
    ("diff_summary", False),
    ("patch_file", False),
    ("changed_file_list", True),
    ("test_results", True),
    ("example_results", False),
    ("claimguard_results", True),
    ("safety_invariant_results", True),
    ("lint_results", False),
    ("typecheck_results", False),
    ("pr_metadata", False),
    ("operator_note", False),
)


@dataclass
class ImplementationArtifact:
    """One declared implementation artifact + its presence status + payload."""

    artifact_id: str
    status: str = ImplementationArtifactStatus.MISSING_WARNING
    required: bool = False
    path: str = ""
    payload: Any = None
    detail: str = ""

    @property
    def present(self) -> bool:
        return self.status in (ImplementationArtifactStatus.PRESENT,
                               ImplementationArtifactStatus.PROVIDED)

    def to_dict(self) -> Dict[str, Any]:
        return {"artifact_id": self.artifact_id, "status": self.status,
                "required": self.required, "path": self.path,
                "present": self.present, "detail": self.detail,
                "has_payload": self.payload is not None}


@dataclass
class ImplementationIntakeManifest:
    """Declares + records the local implementation artifacts to audit."""

    artifacts: Dict[str, ImplementationArtifact] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.artifacts:
            for aid, required in _ARTIFACT_SPEC:
                status = (ImplementationArtifactStatus.MISSING_BLOCKER
                          if required
                          else ImplementationArtifactStatus.MISSING_WARNING)
                self.artifacts[aid] = ImplementationArtifact(
                    artifact_id=aid, status=status, required=required,
                    detail="not supplied")

    def provide(self, artifact_id: str, payload: Any, *, path: str = "",
                status: Optional[str] = None,
                detail: str = "") -> ImplementationArtifact:
        required = (self.artifacts[artifact_id].required
                    if artifact_id in self.artifacts else False)
        art = ImplementationArtifact(
            artifact_id=artifact_id,
            status=status or ImplementationArtifactStatus.PROVIDED,
            required=required, path=path, payload=payload,
            detail=detail or "provided in-memory")
        self.artifacts[artifact_id] = art
        return art

    def get(self, artifact_id: str) -> Any:
        art = self.artifacts.get(artifact_id)
        return art.payload if art and art.present else None

    def operator_note(self) -> Any:
        return self.get("operator_note")

    def blockers(self) -> List[str]:
        return [a.artifact_id for a in self.artifacts.values()
                if a.status in (ImplementationArtifactStatus.MISSING_BLOCKER,
                                ImplementationArtifactStatus.CORRUPT)]

    def warnings(self) -> List[str]:
        return [a.artifact_id for a in self.artifacts.values()
                if a.status in (ImplementationArtifactStatus.MISSING_WARNING,
                                ImplementationArtifactStatus.EMPTY)]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_count": len(self.artifacts),
            "present_count": sum(1 for a in self.artifacts.values()
                                 if a.present),
            "artifacts": {aid: a.to_dict()
                          for aid, a in self.artifacts.items()},
            "blockers": self.blockers(),
            "warnings": self.warnings(),
            "note": ("the intake manifest reads local artifacts only; it never "
                     "calls GitHub, and an operator note never overrides a "
                     "safety failure"),
        }
