"""Claim impact -- how review feedback should change a specific claim.

:class:`ClaimImpactAssessor` maps classified objections and reproduction outcomes
to per-claim impact assessments. Each impact references a specific claim id;
falsification downgrades or blocks; a forbidden-claim risk blocks publication
readiness; and impacts are proposals -- the Scientific Claim Registry remains the
source of truth after any update.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .objection_classifier import ObjectionCategory, ObjectionValidityStatus


class ClaimImpactType:
    STRENGTHEN_CLAIM = "strengthen_claim"
    WEAKEN_CLAIM = "weaken_claim"
    DOWNGRADE_TO_WEAK = "downgrade_to_weak"
    DOWNGRADE_TO_INCONCLUSIVE = "downgrade_to_inconclusive"
    MARK_UNSUPPORTED = "mark_unsupported"
    MARK_CONTRADICTED = "mark_contradicted"
    MARK_FALSIFIED = "mark_falsified"
    MARK_FORBIDDEN = "mark_forbidden"
    REQUIRE_MORE_EVIDENCE = "require_more_evidence"
    REQUIRE_REWORDING = "require_rewording"
    NO_CHANGE = "no_change"
    UNKNOWN = "unknown"

    ALL = (STRENGTHEN_CLAIM, WEAKEN_CLAIM, DOWNGRADE_TO_WEAK,
           DOWNGRADE_TO_INCONCLUSIVE, MARK_UNSUPPORTED, MARK_CONTRADICTED,
           MARK_FALSIFIED, MARK_FORBIDDEN, REQUIRE_MORE_EVIDENCE,
           REQUIRE_REWORDING, NO_CHANGE, UNKNOWN)

    DOWNGRADES = (WEAKEN_CLAIM, DOWNGRADE_TO_WEAK, DOWNGRADE_TO_INCONCLUSIVE,
                  MARK_UNSUPPORTED, MARK_CONTRADICTED, MARK_FALSIFIED,
                  MARK_FORBIDDEN)
    BLOCKS_READINESS = (MARK_FALSIFIED, MARK_FORBIDDEN, MARK_CONTRADICTED)


class ClaimImpactSeverity:
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"

    ALL = (INFO, MINOR, MAJOR, CRITICAL)


# objection category -> claim impact type.
_CATEGORY_IMPACT = {
    ObjectionCategory.MISSING_EVIDENCE: ClaimImpactType.REQUIRE_MORE_EVIDENCE,
    ObjectionCategory.WEAK_EVIDENCE: ClaimImpactType.DOWNGRADE_TO_WEAK,
    ObjectionCategory.FAILED_REPRODUCTION:
        ClaimImpactType.DOWNGRADE_TO_INCONCLUSIVE,
    ObjectionCategory.FIXTURE_OVERFIT: ClaimImpactType.DOWNGRADE_TO_WEAK,
    ObjectionCategory.HUMAN_LABEL_CONTAMINATION:
        ClaimImpactType.REQUIRE_MORE_EVIDENCE,
    ObjectionCategory.PASSIVE_PARSER_ALTERNATIVE:
        ClaimImpactType.DOWNGRADE_TO_INCONCLUSIVE,
    ObjectionCategory.LOG_ACCUMULATION_ALTERNATIVE:
        ClaimImpactType.DOWNGRADE_TO_INCONCLUSIVE,
    ObjectionCategory.INSUFFICIENT_CONTROLS: ClaimImpactType.WEAKEN_CLAIM,
    ObjectionCategory.INSUFFICIENT_REPLICATION: ClaimImpactType.WEAKEN_CLAIM,
    ObjectionCategory.UNSUPPORTED_CLAIM: ClaimImpactType.MARK_UNSUPPORTED,
    ObjectionCategory.FORBIDDEN_CLAIM_RISK: ClaimImpactType.MARK_FORBIDDEN,
    ObjectionCategory.UNCLEAR_METHOD: ClaimImpactType.REQUIRE_REWORDING,
    ObjectionCategory.UNCLEAR_METRIC: ClaimImpactType.REQUIRE_REWORDING,
    ObjectionCategory.INTERPRETATION_CONCERN: ClaimImpactType.REQUIRE_REWORDING,
    ObjectionCategory.STATISTICAL_CONCERN: ClaimImpactType.REQUIRE_MORE_EVIDENCE,
    ObjectionCategory.BASELINE_CONCERN: ClaimImpactType.WEAKEN_CLAIM,
    ObjectionCategory.DOCUMENTATION_CONCERN: ClaimImpactType.NO_CHANGE,
}


@dataclass
class ClaimImpactAssessment:
    """One per-claim impact (a proposal; the registry stays source of truth)."""

    claim_id: str
    impact_type: str = ClaimImpactType.NO_CHANGE
    severity: str = ClaimImpactSeverity.MINOR
    source_objection_id: str = ""
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.impact_type not in ClaimImpactType.ALL:
            self.impact_type = ClaimImpactType.UNKNOWN
        if self.severity not in ClaimImpactSeverity.ALL:
            self.severity = ClaimImpactSeverity.MINOR

    @property
    def is_downgrade(self) -> bool:
        return self.impact_type in ClaimImpactType.DOWNGRADES

    @property
    def blocks_readiness(self) -> bool:
        return self.impact_type in ClaimImpactType.BLOCKS_READINESS

    def to_dict(self) -> Dict[str, Any]:
        return {"claim_id": self.claim_id, "impact_type": self.impact_type,
                "severity": self.severity,
                "source_objection_id": self.source_objection_id,
                "rationale": self.rationale, "is_downgrade": self.is_downgrade,
                "blocks_readiness": self.blocks_readiness, "is_proposal": True}


@dataclass
class ClaimImpactAssessor:
    """Derives per-claim impact from classified objections + reproductions."""

    def assess(self, *, objections: List[Any],
               reproductions: Optional[List[Any]] = None,
               ) -> List[ClaimImpactAssessment]:
        out: List[ClaimImpactAssessment] = []
        for c in objections:
            impact_type = _CATEGORY_IMPACT.get(c.category, ClaimImpactType.UNKNOWN)
            if c.validity == ObjectionValidityStatus.ACCEPTED_AS_FALSIFICATION:
                impact_type = ClaimImpactType.MARK_FALSIFIED
            elif c.validity == ObjectionValidityStatus.INVALID_WITH_EVIDENCE:
                impact_type = ClaimImpactType.NO_CHANGE
            elif c.validity == ObjectionValidityStatus.ACCEPTED_AS_LIMITATION:
                # An accepted limitation weakens but does not block.
                if impact_type in ClaimImpactType.BLOCKS_READINESS and \
                        impact_type != ClaimImpactType.MARK_FALSIFIED:
                    impact_type = ClaimImpactType.WEAKEN_CLAIM
            severity = (ClaimImpactSeverity.CRITICAL if c.critical
                        else ClaimImpactSeverity.MAJOR if c.severity == "major"
                        else ClaimImpactSeverity.MINOR)
            for claim_id in (c.claim_refs or [""]):
                out.append(ClaimImpactAssessment(
                    claim_id=claim_id, impact_type=impact_type,
                    severity=severity, source_objection_id=c.objection_id,
                    rationale=f"from objection {c.category}: {c.text[:80]}"))
        for o in (reproductions or []):
            if o.is_failure:
                for claim_id in (o.claim_refs or [""]):
                    out.append(ClaimImpactAssessment(
                        claim_id=claim_id,
                        impact_type=ClaimImpactType.DOWNGRADE_TO_INCONCLUSIVE,
                        severity=ClaimImpactSeverity.MAJOR,
                        rationale=f"failed reproduction of {o.challenge_type}"))
        return out

    @staticmethod
    def summary(impacts: List[ClaimImpactAssessment]) -> Dict[str, Any]:
        downgrades = [i for i in impacts if i.is_downgrade]
        falsifications = [i for i in impacts
                          if i.impact_type == ClaimImpactType.MARK_FALSIFIED]
        forbidden = [i for i in impacts
                     if i.impact_type == ClaimImpactType.MARK_FORBIDDEN]
        return {
            "claim_impact_count": len(impacts),
            "claim_downgrade_count": len(downgrades),
            "claim_falsification_count": len(falsifications),
            "claim_forbidden_count": len(forbidden),
            "blocks_readiness": any(i.blocks_readiness for i in impacts),
            "impacts": [i.to_dict() for i in impacts],
            "note": "claim impacts reference specific claim ids; falsification "
                    "downgrades or blocks; forbidden risk blocks publication "
                    "readiness; impacts are proposals and the Scientific Claim "
                    "Registry remains the source of truth",
        }
