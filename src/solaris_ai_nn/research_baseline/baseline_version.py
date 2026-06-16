"""Research baseline version -- local metadata, not a Git tag or release.

:class:`ResearchBaselineVersion` assigns a *local* version id to a validated (or
validated-with-warnings) post-merge baseline and records its provenance and
evidence refs. The version id is local metadata: it creates no Git tag, no GitHub
release, no branch, and calls no Git/GitHub. A blocked baseline can never become
a validated version.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class BaselineVersionStatus:
    DRAFT = "draft"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    VALIDATED_WITH_WARNINGS = "validated_with_warnings"
    BLOCKED = "blocked"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"

    ALL = (DRAFT, CANDIDATE, VALIDATED, VALIDATED_WITH_WARNINGS, BLOCKED,
           ARCHIVED, SUPERSEDED, UNKNOWN)

    VALIDATED_KINDS = (VALIDATED, VALIDATED_WITH_WARNINGS)


@dataclass
class BaselineVersionRecord:
    """The full provenance + evidence record for one research baseline version."""

    baseline_version_id: str
    parent_baseline_id: str = ""
    candidate_baseline_id: str = ""
    source_post_merge_report: str = ""
    source_baseline_registry_entry: str = ""
    operator_confirmation_refs: List[str] = field(default_factory=list)
    architecture_evidence_refs: List[str] = field(default_factory=list)
    validation_refs: List[str] = field(default_factory=list)
    safety_refs: List[str] = field(default_factory=list)
    known_warnings: List[str] = field(default_factory=list)
    known_blockers: List[str] = field(default_factory=list)
    recommended_use: str = ""
    status: str = BaselineVersionStatus.DRAFT
    limitations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_ts: float = field(default_factory=time.time)

    @property
    def validated(self) -> bool:
        return self.status in BaselineVersionStatus.VALIDATED_KINDS

    @property
    def blocked(self) -> bool:
        return self.status == BaselineVersionStatus.BLOCKED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_version_id": self.baseline_version_id,
            "parent_baseline_id": self.parent_baseline_id,
            "candidate_baseline_id": self.candidate_baseline_id,
            "source_post_merge_report": self.source_post_merge_report,
            "source_baseline_registry_entry":
                self.source_baseline_registry_entry,
            "operator_confirmation_refs":
                list(self.operator_confirmation_refs),
            "architecture_evidence_refs": list(self.architecture_evidence_refs),
            "validation_refs": list(self.validation_refs),
            "safety_refs": list(self.safety_refs),
            "known_warnings": list(self.known_warnings),
            "known_blockers": list(self.known_blockers),
            "recommended_use": self.recommended_use,
            "status": self.status,
            "limitations": list(self.limitations),
            "metadata": dict(self.metadata),
            "validated": self.validated, "blocked": self.blocked,
            "created_ts": self.created_ts,
            "is_git_tag": False, "is_github_release": False,
            "is_product_release": False,
        }


@dataclass
class ResearchBaselineVersion:
    """Assigns a local version id + status to a candidate baseline."""

    def assign(self, *, baseline_version_id: str,
               candidate_baseline_id: str = "",
               parent_baseline_id: str = "",
               requested_status: str = BaselineVersionStatus.CANDIDATE,
               known_warnings: Optional[List[str]] = None,
               known_blockers: Optional[List[str]] = None,
               critical_safety_failed: bool = False,
               required_validation_missing: bool = False,
               **fields) -> BaselineVersionRecord:
        known_warnings = list(known_warnings or [])
        known_blockers = list(known_blockers or [])

        # A blocked baseline (or one with critical safety / missing required
        # validation) can never become a validated version.
        if known_blockers or critical_safety_failed:
            status = BaselineVersionStatus.BLOCKED
        elif required_validation_missing and requested_status in \
                BaselineVersionStatus.VALIDATED_KINDS:
            status = BaselineVersionStatus.CANDIDATE
        elif requested_status == BaselineVersionStatus.VALIDATED and \
                known_warnings:
            status = BaselineVersionStatus.VALIDATED_WITH_WARNINGS
        else:
            status = (requested_status if requested_status in
                      BaselineVersionStatus.ALL else
                      BaselineVersionStatus.UNKNOWN)

        recommended = self._recommended_use(status)
        return BaselineVersionRecord(
            baseline_version_id=baseline_version_id,
            candidate_baseline_id=candidate_baseline_id,
            parent_baseline_id=parent_baseline_id,
            known_warnings=known_warnings, known_blockers=known_blockers,
            recommended_use=recommended, status=status, **fields)

    @staticmethod
    def _recommended_use(status: str) -> str:
        return {
            BaselineVersionStatus.VALIDATED:
                "use as the reference baseline for the next experimental cycle",
            BaselineVersionStatus.VALIDATED_WITH_WARNINGS:
                "usable as a reference baseline; review the known warnings first",
            BaselineVersionStatus.BLOCKED:
                "do not use; resolve blockers / collect evidence first",
            BaselineVersionStatus.CANDIDATE:
                "candidate only; complete validation before relying on it",
        }.get(status, "status unknown; treat as candidate")
