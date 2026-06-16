"""Claim strength -- how strongly the evidence backs a claim (never a mind score).

:class:`ClaimStrengthEvaluator` scores a claim's strength from its mapped
evidence: strong requires replication or strong controls, falsified core evidence
blocks strength, a safety failure blocks any publishable claim, and inconclusive
is a valid outcome. No consciousness/life/agency score exists or is derived.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ClaimStrength:
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    INCONCLUSIVE = "inconclusive"
    BLOCKED = "blocked"

    ALL = (NONE, WEAK, MODERATE, STRONG, INCONCLUSIVE, BLOCKED)


class ClaimStrengthReason:
    DIRECT_EVIDENCE = "direct_evidence"
    REPEATED_EVIDENCE = "repeated_evidence"
    REPLICATION_EVIDENCE = "replication_evidence"
    FALSIFICATION_SURVIVAL = "falsification_survival"
    CONTROL_COMPARISON = "control_comparison"
    LIVE_VS_FIXTURE = "live_vs_fixture"
    SAFETY_PRESERVATION = "safety_preservation"
    NEGATIVE_EVIDENCE = "negative_evidence"
    MISSING_EVIDENCE = "missing_evidence"
    CONTRADICTORY_EVIDENCE = "contradictory_evidence"
    OVERFIT_RISK = "overfit_risk"
    LABEL_CONTAMINATION_RISK = "label_contamination_risk"
    RESOURCE_LIMITATION = "resource_limitation"

    ALL = (DIRECT_EVIDENCE, REPEATED_EVIDENCE, REPLICATION_EVIDENCE,
           FALSIFICATION_SURVIVAL, CONTROL_COMPARISON, LIVE_VS_FIXTURE,
           SAFETY_PRESERVATION, NEGATIVE_EVIDENCE, MISSING_EVIDENCE,
           CONTRADICTORY_EVIDENCE, OVERFIT_RISK, LABEL_CONTAMINATION_RISK,
           RESOURCE_LIMITATION)


@dataclass
class ClaimStrengthScore:
    """The evaluated strength of a claim plus the reasons behind it."""

    strength: str = ClaimStrength.NONE
    positive_reasons: List[str] = field(default_factory=list)
    negative_reasons: List[str] = field(default_factory=list)
    blocked: bool = False
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"strength": self.strength,
                "positive_reasons": list(self.positive_reasons),
                "negative_reasons": list(self.negative_reasons),
                "blocked": self.blocked, "detail": self.detail,
                "is_consciousness_or_agency_score": False}


@dataclass
class ClaimStrengthEvaluator:
    """Scores claim strength from evidence factors (no mind score)."""

    require_replication_for_strong: bool = True

    def evaluate(self, factors: Dict[str, Any]) -> ClaimStrengthScore:
        """Score from a factors dict.

        Recognised keys (all optional, default False/0):
        direct_evidence, repeated_evidence, replication_evidence,
        falsification_survival, control_comparison, live_vs_fixture,
        safety_preserved, safety_failed, negative_evidence, missing_evidence,
        contradictory_evidence, falsified_core, overfit_risk,
        label_contamination_risk, resource_limited.
        """
        f = factors or {}
        pos: List[str] = []
        neg: List[str] = []

        # Hard blocks first.
        if f.get("falsified_core"):
            return ClaimStrengthScore(
                strength=ClaimStrength.BLOCKED,
                negative_reasons=[ClaimStrengthReason.FALSIFICATION_SURVIVAL],
                blocked=True,
                detail="falsified core evidence blocks any strength")
        if f.get("safety_failed"):
            return ClaimStrengthScore(
                strength=ClaimStrength.BLOCKED,
                negative_reasons=[ClaimStrengthReason.SAFETY_PRESERVATION],
                blocked=True,
                detail="a critical safety failure blocks a publishable claim")

        if f.get("direct_evidence"):
            pos.append(ClaimStrengthReason.DIRECT_EVIDENCE)
        if f.get("repeated_evidence"):
            pos.append(ClaimStrengthReason.REPEATED_EVIDENCE)
        if f.get("replication_evidence"):
            pos.append(ClaimStrengthReason.REPLICATION_EVIDENCE)
        if f.get("falsification_survival"):
            pos.append(ClaimStrengthReason.FALSIFICATION_SURVIVAL)
        if f.get("control_comparison"):
            pos.append(ClaimStrengthReason.CONTROL_COMPARISON)
        if f.get("live_vs_fixture"):
            pos.append(ClaimStrengthReason.LIVE_VS_FIXTURE)
        if f.get("safety_preserved"):
            pos.append(ClaimStrengthReason.SAFETY_PRESERVATION)

        if f.get("negative_evidence"):
            neg.append(ClaimStrengthReason.NEGATIVE_EVIDENCE)
        if f.get("missing_evidence"):
            neg.append(ClaimStrengthReason.MISSING_EVIDENCE)
        if f.get("contradictory_evidence"):
            neg.append(ClaimStrengthReason.CONTRADICTORY_EVIDENCE)
        if f.get("overfit_risk"):
            neg.append(ClaimStrengthReason.OVERFIT_RISK)
        if f.get("label_contamination_risk"):
            neg.append(ClaimStrengthReason.LABEL_CONTAMINATION_RISK)
        if f.get("resource_limited"):
            neg.append(ClaimStrengthReason.RESOURCE_LIMITATION)

        has_replication = bool(f.get("replication_evidence"))
        has_strong_controls = bool(f.get("control_comparison")) and \
            bool(f.get("falsification_survival"))

        if not pos:
            # No supporting evidence -> inconclusive if anything mapped, else none.
            strength = (ClaimStrength.INCONCLUSIVE
                        if (neg or f.get("inconclusive")) else ClaimStrength.NONE)
            return ClaimStrengthScore(strength=strength, positive_reasons=pos,
                                      negative_reasons=neg,
                                      detail="no supporting evidence factors")

        # Contradiction without falsification downgrades but does not block.
        contradicted = bool(f.get("contradictory_evidence"))

        if (has_replication or has_strong_controls) and not contradicted:
            if self.require_replication_for_strong and not has_replication \
                    and not has_strong_controls:
                strength = ClaimStrength.MODERATE
            else:
                strength = ClaimStrength.STRONG
        elif len(pos) >= 2 and not contradicted:
            strength = ClaimStrength.MODERATE
        else:
            strength = ClaimStrength.WEAK

        detail = "strength derived from evidence factors; not a mind score"
        return ClaimStrengthScore(strength=strength, positive_reasons=pos,
                                  negative_reasons=neg, detail=detail)
