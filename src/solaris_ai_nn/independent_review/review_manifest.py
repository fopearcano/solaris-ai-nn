"""Independent review manifest -- indexes local artifacts for inspection.

:class:`IndependentReviewManifest` indexes the local artifacts an external
reviewer could inspect (baseline report, reproducibility bundle, scientific claim
report, publication dossier, claim registry, theory ledger, evidence map,
counterevidence, limitations, soak/replication/falsification reports, research
cycle report, architecture/intake/post-merge/safety/evaluation reports, fixtures,
synthetic examples, operator notes). It indexes local artifacts only, uploads
nothing, keeps missing artifacts visible, and always includes negative, falsified,
and inconclusive evidence.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


ARTIFACT_CATEGORIES = (
    "research_baseline_report", "reproducibility_bundle",
    "scientific_claim_report", "publication_dossier", "safe_abstracts",
    "claim_registry", "theory_ledger", "evidence_map", "counterevidence_report",
    "limitations_report", "soak_dossier", "replication_report",
    "falsification_report", "research_cycle_report",
    "architecture_evolution_report", "implementation_intake_report",
    "post_merge_assimilation_report", "safety_invariant_report",
    "evaluation_report", "fixture_data", "synthetic_examples", "operator_notes",
    "missing_artifact_marker",
)

# Categories whose presence is critical for a meaningful review.
_CRITICAL = ("scientific_claim_report", "claim_registry", "counterevidence_report",
             "limitations_report", "safety_invariant_report")


class ReviewArtifactStatus:
    PRESENT = "present"
    MISSING = "missing"
    STALE = "stale"
    BLOCKED = "blocked"
    INCONCLUSIVE = "inconclusive"

    ALL = (PRESENT, MISSING, STALE, BLOCKED, INCONCLUSIVE)


class ReviewScope:
    INTERNAL = "internal"
    FRIENDLY_EXTERNAL = "friendly_external"
    HOSTILE_EXTERNAL = "hostile_external"

    ALL = (INTERNAL, FRIENDLY_EXTERNAL, HOSTILE_EXTERNAL)


@dataclass
class ReviewArtifact:
    """One indexed artifact (ref/path only; not copied or uploaded)."""

    category: str
    ref: str = ""
    status: str = ReviewArtifactStatus.PRESENT
    is_negative_or_falsified: bool = False
    detail: str = ""

    def __post_init__(self) -> None:
        if self.category not in ARTIFACT_CATEGORIES:
            self.category = "missing_artifact_marker"
        if self.status not in ReviewArtifactStatus.ALL:
            self.status = ReviewArtifactStatus.MISSING

    @property
    def critical(self) -> bool:
        return self.category in _CRITICAL

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "ref": self.ref,
                "status": self.status,
                "is_negative_or_falsified": self.is_negative_or_falsified,
                "critical": self.critical, "detail": self.detail,
                "uploaded": False}


@dataclass
class IndependentReviewManifest:
    """Indexes local review artifacts; missing artifacts stay visible."""

    state_dir: str = ".solaris_ai_nn_review"
    scope: str = ReviewScope.INTERNAL
    persist: bool = True
    artifacts: List[ReviewArtifact] = field(default_factory=list, init=False)
    created_ts: float = field(default_factory=time.time, init=False)

    @property
    def _manifest_path(self) -> str:
        return os.path.join(self.state_dir, "review_manifest.json")

    @property
    def _index_path(self) -> str:
        return os.path.join(self.state_dir, "review_artifact_index.json")

    def add(self, artifact: ReviewArtifact) -> ReviewArtifact:
        self.artifacts.append(artifact)
        return artifact

    def add_missing(self, category: str, detail: str = "") -> ReviewArtifact:
        return self.add(ReviewArtifact(
            category=category, status=ReviewArtifactStatus.MISSING,
            detail=detail or "artifact not present in the local state"))

    def present(self) -> List[ReviewArtifact]:
        return [a for a in self.artifacts
                if a.status == ReviewArtifactStatus.PRESENT]

    def missing(self) -> List[ReviewArtifact]:
        return [a for a in self.artifacts
                if a.status == ReviewArtifactStatus.MISSING]

    def missing_critical(self) -> List[ReviewArtifact]:
        return [a for a in self.missing() if a.critical]

    def negative_or_falsified(self) -> List[ReviewArtifact]:
        return [a for a in self.artifacts if a.is_negative_or_falsified]

    def index(self) -> Dict[str, Any]:
        return {
            "independent_review_artifact_count": len(self.artifacts),
            "present_artifact_count": len(self.present()),
            "missing_review_artifact_count": len(self.missing()),
            "missing_critical_artifact_count": len(self.missing_critical()),
            "negative_or_falsified_artifact_count":
                len(self.negative_or_falsified()),
            "scope": self.scope,
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
        d["note"] = ("indexes local artifacts only; uploads nothing; missing "
                     "artifacts stay visible and negative/falsified/inconclusive "
                     "evidence is always included")
        return d
