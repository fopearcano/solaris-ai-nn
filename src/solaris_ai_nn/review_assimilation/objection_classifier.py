"""Reviewer objection classifier -- category, severity, validity; never dismissed.

:class:`ReviewerObjectionClassifier` classifies each reviewer objection by category
and severity and assigns a validity status. Objections are never dismissed by
default; "invalid with evidence" requires evidence refs; critical objections block
the relevant claim/readiness status; and accepted falsifications propagate to the
Scientific Claims layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ObjectionCategory:
    MISSING_EVIDENCE = "missing_evidence"
    WEAK_EVIDENCE = "weak_evidence"
    FAILED_REPRODUCTION = "failed_reproduction"
    FIXTURE_OVERFIT = "fixture_overfit"
    HUMAN_LABEL_CONTAMINATION = "human_label_contamination"
    PASSIVE_PARSER_ALTERNATIVE = "passive_parser_alternative"
    LOG_ACCUMULATION_ALTERNATIVE = "log_accumulation_alternative"
    INSUFFICIENT_CONTROLS = "insufficient_controls"
    INSUFFICIENT_REPLICATION = "insufficient_replication"
    UNCLEAR_METHOD = "unclear_method"
    UNCLEAR_METRIC = "unclear_metric"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    FORBIDDEN_CLAIM_RISK = "forbidden_claim_risk"
    SAFETY_BOUNDARY_CONCERN = "safety_boundary_concern"
    IMPLEMENTATION_CONCERN = "implementation_concern"
    BASELINE_CONCERN = "baseline_concern"
    STATISTICAL_CONCERN = "statistical_concern"
    INTERPRETATION_CONCERN = "interpretation_concern"
    DOCUMENTATION_CONCERN = "documentation_concern"
    UNKNOWN = "unknown"

    ALL = (MISSING_EVIDENCE, WEAK_EVIDENCE, FAILED_REPRODUCTION, FIXTURE_OVERFIT,
           HUMAN_LABEL_CONTAMINATION, PASSIVE_PARSER_ALTERNATIVE,
           LOG_ACCUMULATION_ALTERNATIVE, INSUFFICIENT_CONTROLS,
           INSUFFICIENT_REPLICATION, UNCLEAR_METHOD, UNCLEAR_METRIC,
           UNSUPPORTED_CLAIM, FORBIDDEN_CLAIM_RISK, SAFETY_BOUNDARY_CONCERN,
           IMPLEMENTATION_CONCERN, BASELINE_CONCERN, STATISTICAL_CONCERN,
           INTERPRETATION_CONCERN, DOCUMENTATION_CONCERN, UNKNOWN)

    # Categories that are critical (block relevant claim/readiness) by default.
    CRITICAL_BY_DEFAULT = (FORBIDDEN_CLAIM_RISK, SAFETY_BOUNDARY_CONCERN,
                           FAILED_REPRODUCTION)


class ObjectionSeverity:
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"

    ALL = (INFO, MINOR, MAJOR, CRITICAL)


class ObjectionValidityStatus:
    VALID = "valid"
    PARTIALLY_VALID = "partially_valid"
    INVALID_WITH_EVIDENCE = "invalid_with_evidence"
    REQUIRES_MORE_EVIDENCE = "requires_more_evidence"
    ACCEPTED_AS_LIMITATION = "accepted_as_limitation"
    ACCEPTED_AS_FALSIFICATION = "accepted_as_falsification"
    UNRESOLVED = "unresolved"
    UNKNOWN = "unknown"

    ALL = (VALID, PARTIALLY_VALID, INVALID_WITH_EVIDENCE, REQUIRES_MORE_EVIDENCE,
           ACCEPTED_AS_LIMITATION, ACCEPTED_AS_FALSIFICATION, UNRESOLVED,
           UNKNOWN)

    # Validity statuses that still count as open / unresolved.
    OPEN = (VALID, PARTIALLY_VALID, REQUIRES_MORE_EVIDENCE, UNRESOLVED)


# keyword -> category, for heuristic classification of objection text.
_KEYWORDS = (
    ("forbidden", ObjectionCategory.FORBIDDEN_CLAIM_RISK),
    ("conscious", ObjectionCategory.FORBIDDEN_CLAIM_RISK),
    ("not reproduce", ObjectionCategory.FAILED_REPRODUCTION),
    ("could not reproduce", ObjectionCategory.FAILED_REPRODUCTION),
    ("failed to reproduce", ObjectionCategory.FAILED_REPRODUCTION),
    ("overfit", ObjectionCategory.FIXTURE_OVERFIT),
    ("fixture", ObjectionCategory.FIXTURE_OVERFIT),
    ("human label", ObjectionCategory.HUMAN_LABEL_CONTAMINATION),
    ("label leak", ObjectionCategory.HUMAN_LABEL_CONTAMINATION),
    ("passive parser", ObjectionCategory.PASSIVE_PARSER_ALTERNATIVE),
    ("log accumulation", ObjectionCategory.LOG_ACCUMULATION_ALTERNATIVE),
    ("no control", ObjectionCategory.INSUFFICIENT_CONTROLS),
    ("control arm", ObjectionCategory.INSUFFICIENT_CONTROLS),
    ("replicat", ObjectionCategory.INSUFFICIENT_REPLICATION),
    ("unclear method", ObjectionCategory.UNCLEAR_METHOD),
    ("method is unclear", ObjectionCategory.UNCLEAR_METHOD),
    ("metric", ObjectionCategory.UNCLEAR_METRIC),
    ("unsupported", ObjectionCategory.UNSUPPORTED_CLAIM),
    ("no evidence", ObjectionCategory.MISSING_EVIDENCE),
    ("missing evidence", ObjectionCategory.MISSING_EVIDENCE),
    ("weak evidence", ObjectionCategory.WEAK_EVIDENCE),
    ("safety", ObjectionCategory.SAFETY_BOUNDARY_CONCERN),
    ("implementation", ObjectionCategory.IMPLEMENTATION_CONCERN),
    ("baseline", ObjectionCategory.BASELINE_CONCERN),
    ("sample size", ObjectionCategory.STATISTICAL_CONCERN),
    ("statistic", ObjectionCategory.STATISTICAL_CONCERN),
    ("interpret", ObjectionCategory.INTERPRETATION_CONCERN),
    ("documentation", ObjectionCategory.DOCUMENTATION_CONCERN),
    ("undocumented", ObjectionCategory.DOCUMENTATION_CONCERN),
)


@dataclass
class ReviewerObjectionClassification:
    """One classified objection (never dismissed by default)."""

    objection_id: str
    text: str
    category: str = ObjectionCategory.UNKNOWN
    severity: str = ObjectionSeverity.MAJOR
    validity: str = ObjectionValidityStatus.UNRESOLVED
    claim_refs: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    detail: str = ""

    def __post_init__(self) -> None:
        if self.category not in ObjectionCategory.ALL:
            self.category = ObjectionCategory.UNKNOWN
        if self.severity not in ObjectionSeverity.ALL:
            self.severity = ObjectionSeverity.MAJOR
        if self.validity not in ObjectionValidityStatus.ALL:
            self.validity = ObjectionValidityStatus.UNRESOLVED
        # "invalid with evidence" requires evidence refs; otherwise it stays open.
        if self.validity == ObjectionValidityStatus.INVALID_WITH_EVIDENCE \
                and not self.evidence_refs:
            self.validity = ObjectionValidityStatus.REQUIRES_MORE_EVIDENCE

    @property
    def critical(self) -> bool:
        return self.severity == ObjectionSeverity.CRITICAL

    @property
    def open(self) -> bool:
        return self.validity in ObjectionValidityStatus.OPEN

    @property
    def blocks(self) -> bool:
        """A critical, still-open objection blocks the relevant status."""
        return self.critical and self.open

    def to_dict(self) -> Dict[str, Any]:
        return {"objection_id": self.objection_id, "text": self.text,
                "category": self.category, "severity": self.severity,
                "validity": self.validity, "claim_refs": list(self.claim_refs),
                "evidence_refs": list(self.evidence_refs), "detail": self.detail,
                "critical": self.critical, "open": self.open,
                "blocks": self.blocks, "dismissed_by_default": False}


@dataclass
class ReviewerObjectionClassifier:
    """Classifies reviewer objections (category/severity/validity)."""

    def classify_one(self, objection: Dict[str, Any],
                     ) -> ReviewerObjectionClassification:
        text = str(objection.get("text", ""))
        low = text.lower()
        category = str(objection.get("category", "")) or self._infer_category(low)
        severity = str(objection.get("severity", "")) or self._infer_severity(
            category)
        validity = str(objection.get("validity", "")) \
            or ObjectionValidityStatus.UNRESOLVED
        return ReviewerObjectionClassification(
            objection_id=str(objection.get("objection_id", "")),
            text=text, category=category, severity=severity, validity=validity,
            claim_refs=list(objection.get("claim_refs", [])),
            evidence_refs=list(objection.get("evidence_refs", [])),
            detail=str(objection.get("detail", "")))

    def classify(self, objections: List[Dict[str, Any]], *,
                 max_objections: int = 200,
                 ) -> List[ReviewerObjectionClassification]:
        return [self.classify_one(o)
                for o in (objections or [])[:max_objections]]

    @staticmethod
    def _infer_category(low: str) -> str:
        for keyword, category in _KEYWORDS:
            if keyword in low:
                return category
        return ObjectionCategory.UNKNOWN

    @staticmethod
    def _infer_severity(category: str) -> str:
        if category in ObjectionCategory.CRITICAL_BY_DEFAULT:
            return ObjectionSeverity.CRITICAL
        if category in (ObjectionCategory.UNSUPPORTED_CLAIM,
                        ObjectionCategory.MISSING_EVIDENCE,
                        ObjectionCategory.FIXTURE_OVERFIT,
                        ObjectionCategory.INSUFFICIENT_CONTROLS,
                        ObjectionCategory.INSUFFICIENT_REPLICATION):
            return ObjectionSeverity.MAJOR
        if category in (ObjectionCategory.DOCUMENTATION_CONCERN,
                        ObjectionCategory.UNCLEAR_METRIC):
            return ObjectionSeverity.MINOR
        return ObjectionSeverity.MAJOR

    @staticmethod
    def summary(classifications: List[ReviewerObjectionClassification],
                ) -> Dict[str, Any]:
        valid = [c for c in classifications
                 if c.validity == ObjectionValidityStatus.VALID]
        partial = [c for c in classifications
                   if c.validity == ObjectionValidityStatus.PARTIALLY_VALID]
        critical = [c for c in classifications if c.critical]
        unresolved = [c for c in classifications if c.open]
        falsifications = [c for c in classifications
                          if c.validity ==
                          ObjectionValidityStatus.ACCEPTED_AS_FALSIFICATION]
        return {
            "reviewer_objection_count": len(classifications),
            "valid_objection_count": len(valid),
            "partially_valid_objection_count": len(partial),
            "critical_objection_count": len(critical),
            "unresolved_objection_count": len(unresolved),
            "accepted_falsification_count": len(falsifications),
            "critical_unresolved_count": sum(1 for c in critical if c.open),
            "classifications": [c.to_dict() for c in classifications],
            "note": "objections are never dismissed by default; 'invalid with "
                    "evidence' requires evidence refs and critical open "
                    "objections block the relevant status",
        }
