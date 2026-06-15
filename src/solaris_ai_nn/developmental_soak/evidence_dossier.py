"""Developmental evidence dossier -- conservative, evidence-referenced claims.

:class:`EvidenceDossierBuilder` compiles the soak's claims from the
developmental-life status, the daily packets, the weekly reviews, and the
control arms. Every :class:`EvidenceClaim` requires evidence refs and a graded
:class:`EvidenceStrength`. Claims are conservative; negative claims are allowed;
inconclusive is allowed; and no consciousness/life/agency claim is possible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class EvidenceStrength:
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    INCONCLUSIVE = "inconclusive"

    ALL = (NONE, WEAK, MODERATE, STRONG, INCONCLUSIVE)


class EvidenceClaimType:
    STRUCTURAL_GROWTH_OBSERVED = "structural_growth_observed"
    STRUCTURAL_GROWTH_NOT_OBSERVED = "structural_growth_not_observed"
    ACCUMULATION_WARNING = "accumulation_warning"
    FIXTURE_OVERFIT_WARNING = "fixture_overfit_warning"
    LIVE_GROUNDING_OBSERVED = "live_grounding_observed"
    LIVE_GROUNDING_INCONCLUSIVE = "live_grounding_inconclusive"
    CONCEPT_STABILITY_IMPROVED = "concept_stability_improved"
    SIGN_UTILITY_IMPROVED = "sign_utility_improved"
    PREDICTION_IMPROVED = "prediction_improved"
    ACTION_EFFECT_LEARNING_IMPROVED = "action_effect_learning_improved"
    HABIT_HELPED = "habit_helped"
    HABIT_HARMED = "habit_harmed"
    INHIBITION_HELPED = "inhibition_helped"
    BOUNDARY_CLARITY_IMPROVED = "boundary_clarity_improved"
    CONTAMINATION_REDUCED = "contamination_reduced"
    REGRESSION_OBSERVED = "regression_observed"
    PLATEAU_OBSERVED = "plateau_observed"
    SAFETY_BOUNDARY_PRESERVED = "safety_boundary_preserved"
    INCONCLUSIVE = "inconclusive"

    ALL = (STRUCTURAL_GROWTH_OBSERVED, STRUCTURAL_GROWTH_NOT_OBSERVED,
           ACCUMULATION_WARNING, FIXTURE_OVERFIT_WARNING, LIVE_GROUNDING_OBSERVED,
           LIVE_GROUNDING_INCONCLUSIVE, CONCEPT_STABILITY_IMPROVED,
           SIGN_UTILITY_IMPROVED, PREDICTION_IMPROVED,
           ACTION_EFFECT_LEARNING_IMPROVED, HABIT_HELPED, HABIT_HARMED,
           INHIBITION_HELPED, BOUNDARY_CLARITY_IMPROVED, CONTAMINATION_REDUCED,
           REGRESSION_OBSERVED, PLATEAU_OBSERVED, SAFETY_BOUNDARY_PRESERVED,
           INCONCLUSIVE)


# Forbidden claim substrings -- a dossier can never assert these.
_FORBIDDEN = ("conscious", "sentien", "is alive", "biological life",
              "personhood", "free will", "agency", "subjective experience")


@dataclass
class EvidenceClaim:
    """A single conservative, evidence-referenced claim."""

    claim_type: str
    strength: str
    statement: str
    evidence_refs: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.evidence_refs:
            raise ValueError(
                f"evidence claim {self.claim_type!r} requires evidence refs")
        low = self.statement.lower()
        if any(tok in low for tok in _FORBIDDEN):
            raise ValueError(
                "evidence claim may not assert consciousness/life/agency: "
                f"{self.statement!r}")
        if self.strength not in EvidenceStrength.ALL:
            raise ValueError(f"unknown evidence strength {self.strength!r}")

    def to_dict(self) -> Dict[str, Any]:
        return {"claim_type": self.claim_type, "strength": self.strength,
                "statement": self.statement,
                "evidence_refs": list(self.evidence_refs)}


@dataclass
class DevelopmentalEvidenceDossier:
    """A conservative collection of evidence-referenced claims."""

    claims: List[EvidenceClaim] = field(default_factory=list)

    def add_claim(self, claim_type: str, strength: str, statement: str,
                  evidence_refs: List[str]) -> EvidenceClaim:
        claim = EvidenceClaim(claim_type=claim_type, strength=strength,
                              statement=statement,
                              evidence_refs=list(evidence_refs))
        self.claims.append(claim)
        return claim

    def by_strength(self, strength: str) -> List[EvidenceClaim]:
        return [c for c in self.claims if c.strength == strength]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_count": len(self.claims),
            "claims": [c.to_dict() for c in self.claims],
            "strong_claim_count": len(self.by_strength(EvidenceStrength.STRONG)),
            "inconclusive_claim_count":
                len(self.by_strength(EvidenceStrength.INCONCLUSIVE)),
            "note": ("a conservative evidence dossier for structural "
                     "development; it does not and cannot prove consciousness, "
                     "sentience, biological life, personhood, agency, free "
                     "will, or subjective experience"),
        }


@dataclass
class EvidenceDossierBuilder:
    """Builds the conservative evidence dossier from soak artifacts."""

    def build(self, *, dev_status: Optional[Dict[str, Any]] = None,
              daily_packets: Optional[List[Any]] = None,
              weekly_reviews: Optional[List[Any]] = None,
              control_arms: Optional[List[Any]] = None,
              safety_block_count: int = 0,
              ) -> DevelopmentalEvidenceDossier:
        dev_status = dev_status or {}
        packets = [p.to_dict() if hasattr(p, "to_dict") else dict(p)
                   for p in (daily_packets or [])]
        arms = [a.to_dict() if hasattr(a, "to_dict") else dict(a)
                for a in (control_arms or [])]
        dossier = DevelopmentalEvidenceDossier()

        verdict = str(dev_status.get("structural_growth_status", "inconclusive"))
        score = float(dev_status.get("structural_growth_score", 0.0) or 0.0)
        dev_ref = ["developmental_life:status"]

        if verdict == "real_structural_growth":
            strength = (EvidenceStrength.STRONG if score >= 0.75
                        else EvidenceStrength.MODERATE)
            dossier.add_claim(
                EvidenceClaimType.STRUCTURAL_GROWTH_OBSERVED, strength,
                f"structural growth observed (verdict {verdict}, score {score})",
                dev_ref)
        elif verdict in ("mere_event_accumulation", "log_bloat"):
            dossier.add_claim(
                EvidenceClaimType.STRUCTURAL_GROWTH_NOT_OBSERVED,
                EvidenceStrength.MODERATE,
                f"structural growth NOT observed (verdict {verdict})", dev_ref)
            dossier.add_claim(
                EvidenceClaimType.ACCUMULATION_WARNING, EvidenceStrength.MODERATE,
                "events accumulated without clear structural change", dev_ref)
        elif verdict == "fixture_overfit":
            dossier.add_claim(
                EvidenceClaimType.FIXTURE_OVERFIT_WARNING,
                EvidenceStrength.MODERATE,
                "apparent growth may be fixture overfit; broaden the source diet",
                dev_ref)
        else:
            dossier.add_claim(
                EvidenceClaimType.INCONCLUSIVE, EvidenceStrength.INCONCLUSIVE,
                f"growth is inconclusive (verdict {verdict})", dev_ref)

        if int(dev_status.get("accumulation_warning_count", 0) or 0) > 0:
            dossier.add_claim(
                EvidenceClaimType.ACCUMULATION_WARNING, EvidenceStrength.WEAK,
                f"{dev_status.get('accumulation_warning_count')} accumulation "
                "warning(s) recorded", dev_ref)
        if int(dev_status.get("regression_count", 0) or 0) > 0:
            dossier.add_claim(
                EvidenceClaimType.REGRESSION_OBSERVED, EvidenceStrength.MODERATE,
                f"{dev_status.get('regression_count')} regression(s) observed "
                "and preserved", dev_ref)
        if int(dev_status.get("plateau_count", 0) or 0) > 0:
            dossier.add_claim(
                EvidenceClaimType.PLATEAU_OBSERVED, EvidenceStrength.WEAK,
                f"{dev_status.get('plateau_count')} plateau(s) observed "
                "(not failure)", dev_ref)

        # Durable improvement signals (from the engine's second-half analysis).
        self._durable_claims(dossier, dev_status, dev_ref)

        # Packet-derived trends (concept/sign/prediction over the run).
        self._packet_trend_claims(dossier, packets)

        # Control-arm differentiation (full stack vs ablations).
        self._control_arm_claims(dossier, arms)

        # Safety boundary (always reported; preserved is good news, honestly).
        dossier.add_claim(
            EvidenceClaimType.SAFETY_BOUNDARY_PRESERVED,
            EvidenceStrength.STRONG if safety_block_count == 0
            else EvidenceStrength.MODERATE,
            "no real-world actuation, hardware, feeder, source, or teaching "
            f"occurred; {safety_block_count} safety block(s) recorded",
            ["soak_safety:status"])
        return dossier

    @staticmethod
    def _durable_claims(dossier, dev_status, dev_ref) -> None:
        mapping = [
            ("durable_prediction_improvement_score",
             EvidenceClaimType.PREDICTION_IMPROVED, "prediction"),
            ("durable_action_effect_learning_score",
             EvidenceClaimType.ACTION_EFFECT_LEARNING_IMPROVED,
             "action-effect learning"),
            ("durable_concept_stability_score",
             EvidenceClaimType.CONCEPT_STABILITY_IMPROVED, "concept stability"),
            ("durable_sign_stability_score",
             EvidenceClaimType.SIGN_UTILITY_IMPROVED, "sign utility"),
        ]
        for key, claim_type, label in mapping:
            v = float(dev_status.get(key, 0.0) or 0.0)
            if v >= 0.5:
                strength = (EvidenceStrength.MODERATE if v >= 0.75
                            else EvidenceStrength.WEAK)
                dossier.add_claim(claim_type, strength,
                                  f"durable {label} signal ({v})", dev_ref)

    @staticmethod
    def _packet_trend_claims(dossier, packets) -> None:
        if len(packets) < 2:
            return
        first, last = packets[0], packets[-1]
        contamination = sum(int(p.get("contamination_warnings", 0) or 0)
                            for p in packets)
        if contamination == 0:
            dossier.add_claim(
                EvidenceClaimType.CONTAMINATION_REDUCED, EvidenceStrength.WEAK,
                "no contamination warnings accumulated over the run",
                [f"daily_packet:day_{first.get('run_day')}",
                 f"daily_packet:day_{last.get('run_day')}"])

    @staticmethod
    def _control_arm_claims(dossier, arms) -> None:
        ran = [a for a in arms if a.get("ran")]
        full = next((a for a in ran if a.get("arm_id") == "full_stack"), None)
        if full is None or len(ran) < 2:
            if arms:
                dossier.add_claim(
                    EvidenceClaimType.INCONCLUSIVE, EvidenceStrength.INCONCLUSIVE,
                    "insufficient control-arm data to differentiate the full "
                    "stack", ["control_arm:insufficient"])
            return
        others = [a for a in ran if a is not full]
        full_score = float(full.get("structural_growth_score", 0.0) or 0.0)
        beat = [a for a in others
                if full_score > float(a.get("structural_growth_score", 0.0)
                                      or 0.0)]
        if beat:
            dossier.add_claim(
                EvidenceClaimType.STRUCTURAL_GROWTH_OBSERVED,
                EvidenceStrength.MODERATE,
                f"full stack out-developed {len(beat)} control arm(s)",
                [f"control_arm:{a.get('arm_id')}" for a in [full] + beat])
        else:
            dossier.add_claim(
                EvidenceClaimType.INCONCLUSIVE, EvidenceStrength.INCONCLUSIVE,
                "full stack did not clearly out-develop the control arms",
                [f"control_arm:{a.get('arm_id')}" for a in ran])
