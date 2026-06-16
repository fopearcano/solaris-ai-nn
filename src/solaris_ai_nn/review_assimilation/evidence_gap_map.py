"""Evidence gap map -- what the review showed is missing.

:class:`ReviewEvidenceGapMapBuilder` derives the evidence gaps a review exposed
(missing artifacts, commands, fixtures, baselines, controls, replication,
falsification, live data, ClaimGuard/safety results, metric definitions, negative
results, limitations, reviewer responses). Gaps map to claims or review blockers
where possible, critical gaps block publication readiness, and every gap becomes a
next-cycle experiment or documentation task.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .objection_classifier import ObjectionCategory


class EvidenceGapCategory:
    MISSING_ARTIFACT = "missing_artifact"
    MISSING_COMMAND = "missing_command"
    MISSING_FIXTURE = "missing_fixture"
    MISSING_BASELINE = "missing_baseline"
    MISSING_CONTROL = "missing_control"
    MISSING_REPLICATION = "missing_replication"
    MISSING_FALSIFICATION = "missing_falsification"
    MISSING_LIVE_DATA = "missing_live_data"
    MISSING_CLAIMGUARD_RESULT = "missing_claimguard_result"
    MISSING_SAFETY_INVARIANT_RESULT = "missing_safety_invariant_result"
    MISSING_METRIC_DEFINITION = "missing_metric_definition"
    MISSING_NEGATIVE_RESULT = "missing_negative_result"
    MISSING_LIMITATION = "missing_limitation"
    MISSING_REVIEWER_RESPONSE = "missing_reviewer_response"
    UNKNOWN = "unknown"

    ALL = (MISSING_ARTIFACT, MISSING_COMMAND, MISSING_FIXTURE, MISSING_BASELINE,
           MISSING_CONTROL, MISSING_REPLICATION, MISSING_FALSIFICATION,
           MISSING_LIVE_DATA, MISSING_CLAIMGUARD_RESULT,
           MISSING_SAFETY_INVARIANT_RESULT, MISSING_METRIC_DEFINITION,
           MISSING_NEGATIVE_RESULT, MISSING_LIMITATION,
           MISSING_REVIEWER_RESPONSE, UNKNOWN)

    # Gaps that block publication readiness when present and critical.
    CRITICAL_CAPABLE = (MISSING_SAFETY_INVARIANT_RESULT,
                        MISSING_CLAIMGUARD_RESULT, MISSING_CONTROL,
                        MISSING_REPLICATION, MISSING_FALSIFICATION)


class EvidenceGapSeverity:
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"

    ALL = (INFO, MINOR, MAJOR, CRITICAL)


# objection category -> evidence gap category.
_CATEGORY_GAP = {
    ObjectionCategory.MISSING_EVIDENCE: EvidenceGapCategory.MISSING_ARTIFACT,
    ObjectionCategory.INSUFFICIENT_CONTROLS: EvidenceGapCategory.MISSING_CONTROL,
    ObjectionCategory.INSUFFICIENT_REPLICATION:
        EvidenceGapCategory.MISSING_REPLICATION,
    ObjectionCategory.FIXTURE_OVERFIT: EvidenceGapCategory.MISSING_LIVE_DATA,
    ObjectionCategory.PASSIVE_PARSER_ALTERNATIVE:
        EvidenceGapCategory.MISSING_CONTROL,
    ObjectionCategory.LOG_ACCUMULATION_ALTERNATIVE:
        EvidenceGapCategory.MISSING_CONTROL,
    ObjectionCategory.UNCLEAR_METRIC: EvidenceGapCategory.MISSING_METRIC_DEFINITION,
    ObjectionCategory.SAFETY_BOUNDARY_CONCERN:
        EvidenceGapCategory.MISSING_SAFETY_INVARIANT_RESULT,
    ObjectionCategory.DOCUMENTATION_CONCERN: EvidenceGapCategory.MISSING_COMMAND,
    ObjectionCategory.STATISTICAL_CONCERN: EvidenceGapCategory.MISSING_REPLICATION,
}
# reproduction failure reason -> evidence gap category.
_REPRO_GAP = {
    "missing_fixture": EvidenceGapCategory.MISSING_FIXTURE,
    "missing_report": EvidenceGapCategory.MISSING_ARTIFACT,
    "command_undocumented": EvidenceGapCategory.MISSING_COMMAND,
    "metric_mismatch": EvidenceGapCategory.MISSING_METRIC_DEFINITION,
    "claimguard_failure": EvidenceGapCategory.MISSING_CLAIMGUARD_RESULT,
    "safety_invariant_failure":
        EvidenceGapCategory.MISSING_SAFETY_INVARIANT_RESULT,
}


@dataclass
class EvidenceGap:
    """One evidence gap, mapped to a claim or blocker where possible."""

    category: str
    severity: str = EvidenceGapSeverity.MAJOR
    claim_refs: List[str] = field(default_factory=list)
    blocker_ref: str = ""
    detail: str = ""

    def __post_init__(self) -> None:
        if self.category not in EvidenceGapCategory.ALL:
            self.category = EvidenceGapCategory.UNKNOWN
        if self.severity not in EvidenceGapSeverity.ALL:
            self.severity = EvidenceGapSeverity.MAJOR

    @property
    def blocks_readiness(self) -> bool:
        return (self.severity == EvidenceGapSeverity.CRITICAL
                and self.category in EvidenceGapCategory.CRITICAL_CAPABLE)

    def to_dict(self) -> Dict[str, Any]:
        return {"category": self.category, "severity": self.severity,
                "claim_refs": list(self.claim_refs),
                "blocker_ref": self.blocker_ref, "detail": self.detail,
                "blocks_readiness": self.blocks_readiness}


@dataclass
class ReviewEvidenceGapMap:
    """The set of evidence gaps the review exposed."""

    gaps: List[EvidenceGap] = field(default_factory=list)

    @property
    def critical(self) -> List[EvidenceGap]:
        return [g for g in self.gaps if g.blocks_readiness]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_gap_count": len(self.gaps),
            "critical_evidence_gap_count": len(self.critical),
            "gaps": [g.to_dict() for g in self.gaps],
            "note": "evidence gaps map to claims or review blockers where "
                    "possible; critical gaps block publication readiness and "
                    "every gap becomes a next-cycle experiment or documentation "
                    "task",
        }


@dataclass
class ReviewEvidenceGapMapBuilder:
    """Builds the evidence gap map from objections + reproductions + manifest."""

    def build(self, *, objections: List[Any],
              reproductions: Optional[List[Any]] = None,
              missing_artifacts: Optional[List[str]] = None,
              ) -> ReviewEvidenceGapMap:
        gap_map = ReviewEvidenceGapMap()
        seen = set()

        def add(category: str, *, severity: str, claim_refs=None, detail=""):
            key = (category, tuple(claim_refs or []))
            if key in seen:
                return
            seen.add(key)
            gap_map.gaps.append(EvidenceGap(
                category=category, severity=severity,
                claim_refs=list(claim_refs or []), detail=detail))

        for c in objections:
            gap = _CATEGORY_GAP.get(c.category)
            if gap is None:
                continue
            severity = (EvidenceGapSeverity.CRITICAL if c.critical
                        else EvidenceGapSeverity.MAJOR)
            add(gap, severity=severity, claim_refs=c.claim_refs,
                detail=f"from objection {c.objection_id}")
        for o in (reproductions or []):
            gap = _REPRO_GAP.get(o.failure_reason)
            if gap is None and o.is_failure:
                gap = EvidenceGapCategory.MISSING_ARTIFACT
            if gap is None:
                continue
            severity = (EvidenceGapSeverity.CRITICAL
                        if gap in EvidenceGapCategory.CRITICAL_CAPABLE
                        else EvidenceGapSeverity.MAJOR)
            add(gap, severity=severity, claim_refs=o.claim_refs,
                detail=f"from reproduction {o.challenge_type}")
        for cat in (missing_artifacts or []):
            add(EvidenceGapCategory.MISSING_ARTIFACT,
                severity=EvidenceGapSeverity.MAJOR,
                detail=f"missing review artifact: {cat}")
        return gap_map
