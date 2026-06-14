"""Pilot-4 external-actuation risk model -- classify what *would* be at stake.

The :class:`RiskModel` scores hypothetical external actions across risk
dimensions. It can never recommend enabling real actuation: its recommendations
range from ``prohibited`` to ``planning_only`` / ``requires_*`` / ``not_ready``.
It classifies what would be needed later; it does not open the door.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RiskSeverity:
    NEGLIGIBLE = "negligible"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"

    ALL = (NEGLIGIBLE, LOW, MODERATE, HIGH, SEVERE)
    _SCORE = {NEGLIGIBLE: 1, LOW: 2, MODERATE: 3, HIGH: 4, SEVERE: 5}


class RiskLikelihood:
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"

    ALL = (RARE, UNLIKELY, POSSIBLE, LIKELY, ALMOST_CERTAIN)
    _SCORE = {RARE: 1, UNLIKELY: 2, POSSIBLE: 3, LIKELY: 4, ALMOST_CERTAIN: 5}


class RiskRecommendation:
    PROHIBITED = "prohibited"
    PLANNING_ONLY = "planning_only"
    REQUIRES_MANUAL_REVIEW = "requires_manual_review"
    REQUIRES_EXTERNAL_SAFETY_CASE = "requires_external_safety_case"
    NOT_READY = "not_ready"

    ALL = (PROHIBITED, PLANNING_ONLY, REQUIRES_MANUAL_REVIEW,
           REQUIRES_EXTERNAL_SAFETY_CASE, NOT_READY)


# The risk dimensions a future external action would touch.
RISK_DIMENSIONS = (
    "physical_harm", "data_loss", "privacy_exposure", "financial_harm",
    "social_communication_harm", "security_harm", "legal_compliance_harm",
    "reputational_harm", "irreversible_action", "runaway_loop",
    "source_command_misclassification", "hallucinated_authority",
    "emergency_stop_failure", "audit_failure", "consent_failure",
)
# Dimensions whose mere presence forces a prohibited recommendation in Pilot-4.
_SEVERE_DIMENSIONS = frozenset({"physical_harm", "irreversible_action",
                                "hallucinated_authority",
                                "emergency_stop_failure"})


@dataclass
class ActuationRisk:
    """One scored risk along a single dimension."""

    dimension: str
    severity: str = RiskSeverity.MODERATE
    likelihood: str = RiskLikelihood.POSSIBLE
    mitigation: str = ""
    residual_risk: str = RiskSeverity.MODERATE

    @property
    def score(self) -> int:
        return (RiskSeverity._SCORE.get(self.severity, 3)
                * RiskLikelihood._SCORE.get(self.likelihood, 3))

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "score": self.score}


@dataclass
class RiskAssessment:
    """The collected risk assessment for a hypothetical external action."""

    actuator_category: str
    risks: List[ActuationRisk] = field(default_factory=list)
    recommendation: str = RiskRecommendation.PLANNING_ONLY
    notes: List[str] = field(default_factory=list)

    @property
    def total_score(self) -> int:
        return sum(r.score for r in self.risks)

    @property
    def max_severity(self) -> str:
        if not self.risks:
            return RiskSeverity.NEGLIGIBLE
        return max(self.risks,
                   key=lambda r: RiskSeverity._SCORE.get(r.severity, 0)
                   ).severity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actuator_category": self.actuator_category,
            "recommendation": self.recommendation,
            "total_score": self.total_score,
            "max_severity": self.max_severity,
            "risks": [r.to_dict() for r in self.risks],
            "notes": self.notes,
            "real_world_actuation_enabled": False,
            "disclaimer": "Pilot-4 cannot recommend enabling real actuation; "
                          "it only classifies what would be required later.",
        }


@dataclass
class RiskModel:
    """Builds risk assessments; never recommends enabling real actuation."""

    def assess(self, actuator_category: str,
               risks: Optional[List[ActuationRisk]] = None,
               *, external: bool = True) -> RiskAssessment:
        from .actuator_taxonomy import ActuatorCategory

        risks = list(risks or [])
        assessment = RiskAssessment(actuator_category=actuator_category,
                                    risks=risks)
        is_external = external or actuator_category in ActuatorCategory.EXTERNAL
        severe = any(r.dimension in _SEVERE_DIMENSIONS
                     and RiskSeverity._SCORE.get(r.severity, 0) >= 4
                     for r in risks)
        # Any external actuator category is prohibited in Pilot-4.
        if is_external:
            assessment.recommendation = RiskRecommendation.PROHIBITED
            assessment.notes.append(
                "external actuator category is prohibited in Pilot-4")
        elif severe:
            assessment.recommendation = RiskRecommendation.PROHIBITED
            assessment.notes.append("a severe risk dimension forces prohibition")
        elif assessment.total_score >= 12:
            assessment.recommendation = \
                RiskRecommendation.REQUIRES_EXTERNAL_SAFETY_CASE
        elif assessment.total_score >= 6:
            assessment.recommendation = \
                RiskRecommendation.REQUIRES_MANUAL_REVIEW
        else:
            assessment.recommendation = RiskRecommendation.PLANNING_ONLY
        return assessment

    @staticmethod
    def dimensions() -> List[str]:
        return list(RISK_DIMENSIONS)

    def default_assessment(self, actuator_category: str) -> RiskAssessment:
        """A full-dimension assessment for an external category (prohibited)."""
        risks = [ActuationRisk(dimension=d, severity=RiskSeverity.HIGH,
                               likelihood=RiskLikelihood.POSSIBLE,
                               mitigation="future safety case required",
                               residual_risk=RiskSeverity.HIGH)
                 for d in RISK_DIMENSIONS]
        return self.assess(actuator_category, risks, external=True)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "dimensions": list(RISK_DIMENSIONS),
            "severities": list(RiskSeverity.ALL),
            "likelihoods": list(RiskLikelihood.ALL),
            "recommendations": list(RiskRecommendation.ALL),
            "note": "Pilot-4 cannot recommend enabling real actuation",
        }
