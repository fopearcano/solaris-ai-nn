"""Research snapshot manifest -- index the evidence behind a baseline.

:class:`ResearchSnapshotManifest` indexes the artifacts that constitute a research
baseline (reports from every prior module, validation/example/ClaimGuard results,
operator notes). It indexes artifacts only -- it does not copy large artifacts
unless explicitly configured. Missing, corrupt, and negative/falsified/
inconclusive artifacts are all kept visible.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SnapshotArtifactStatus:
    PRESENT = "present"
    PROVIDED = "provided"
    MISSING = "missing"
    CORRUPT = "corrupt"

    ALL = (PRESENT, PROVIDED, MISSING, CORRUPT)


# Canonical artifact types a research baseline snapshot indexes.
ARTIFACT_TYPES = (
    "baseline_registry", "post_merge_assimilation_report",
    "implementation_intake_report", "experiment_compiler_spec",
    "architecture_evolution_report", "replication_report",
    "falsification_report", "soak_dossier", "developmental_life_report",
    "sensorium_reports", "metabolism_report", "ontogenesis_report",
    "semiogenesis_report", "cognition_report", "self_boundary_report",
    "desire_report", "action_reaction_report", "safety_invariant_report",
    "evaluation_report", "operator_notes", "test_results", "example_results",
    "claimguard_results",
)


@dataclass
class SnapshotArtifact:
    """One indexed artifact (path/payload + presence; never silently dropped)."""

    artifact_type: str
    status: str = SnapshotArtifactStatus.MISSING
    path: str = ""
    checksum: str = ""
    negative_evidence: bool = False
    detail: str = ""

    @property
    def present(self) -> bool:
        return self.status in (SnapshotArtifactStatus.PRESENT,
                               SnapshotArtifactStatus.PROVIDED)

    def to_dict(self) -> Dict[str, Any]:
        return {"artifact_type": self.artifact_type, "status": self.status,
                "path": self.path, "checksum": self.checksum,
                "present": self.present,
                "negative_evidence": self.negative_evidence,
                "detail": self.detail}


@dataclass
class ResearchSnapshotManifest:
    """Indexes the artifacts behind a research baseline (index only)."""

    artifacts: Dict[str, SnapshotArtifact] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.artifacts:
            for atype in ARTIFACT_TYPES:
                self.artifacts[atype] = SnapshotArtifact(
                    artifact_type=atype, status=SnapshotArtifactStatus.MISSING,
                    detail="not supplied")

    def index(self, artifact_type: str, *, path: str = "",
              payload: Any = None, negative_evidence: bool = False,
              checksum: str = "") -> SnapshotArtifact:
        status = SnapshotArtifactStatus.MISSING
        detail = "not supplied"
        if path and os.path.isfile(path):
            status = SnapshotArtifactStatus.PRESENT
            detail = "indexed on disk"
            checksum = checksum or self._checksum(path)
        elif path:
            status = SnapshotArtifactStatus.MISSING
            detail = f"declared path not found: {path!r}"
        elif payload is not None:
            status = SnapshotArtifactStatus.PROVIDED
            detail = "indexed in-memory"
        art = SnapshotArtifact(artifact_type=artifact_type, status=status,
                               path=path, checksum=checksum,
                               negative_evidence=negative_evidence,
                               detail=detail)
        self.artifacts[artifact_type] = art
        return art

    def mark_corrupt(self, artifact_type: str, detail: str = "") -> None:
        art = self.artifacts.get(artifact_type) or SnapshotArtifact(
            artifact_type=artifact_type)
        art.status = SnapshotArtifactStatus.CORRUPT
        art.detail = detail or "artifact corrupt (preserved as evidence)"
        self.artifacts[artifact_type] = art

    @staticmethod
    def _checksum(path: str) -> str:
        import hashlib

        try:
            with open(path, "rb") as fh:
                return hashlib.sha256(fh.read()).hexdigest()[:16]
        except Exception:
            return ""

    def missing(self) -> List[str]:
        return [a.artifact_type for a in self.artifacts.values()
                if a.status == SnapshotArtifactStatus.MISSING]

    def corrupt(self) -> List[str]:
        return [a.artifact_type for a in self.artifacts.values()
                if a.status == SnapshotArtifactStatus.CORRUPT]

    def negative_evidence(self) -> List[str]:
        return [a.artifact_type for a in self.artifacts.values()
                if a.negative_evidence]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_artifact_count": sum(1 for a in self.artifacts.values()
                                           if a.present),
            "artifacts": {t: a.to_dict() for t, a in self.artifacts.items()},
            "missing": self.missing(),
            "missing_snapshot_artifact_count": len(self.missing()),
            "corrupt": self.corrupt(),
            "negative_evidence_artifacts": self.negative_evidence(),
            "note": "indexes artifacts only; missing/corrupt and negative/"
                    "falsified/inconclusive artifacts are kept visible",
        }
