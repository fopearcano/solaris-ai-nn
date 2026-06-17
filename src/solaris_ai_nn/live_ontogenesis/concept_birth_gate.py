"""Live concept birth gate -- conservative, evidence-grounded, advisory.

:class:`LiveConceptBirthGate` decides whether a proto-concept candidate may be
*born* (recorded as an operational proto-concept), held as a stable candidate,
deferred, rejected, or blocked. Birth requires valid governance, a birth
certificate, an unblocked observation stability gate, real accepted-event evidence,
recurrence and stability above threshold, contamination below threshold, no
forbidden source, no command contamination, no severe overload/deprivation, no
operator-text dominance, at least one non-human-label feature signature, and more
supporting evidence than counterevidence.

The gate is conservative. It does not enable semiogenesis, create language, or claim
understanding -- it produces only operational proto-concept records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ConceptBirthGateStatus:
    BORN = "born"
    STABLE_CANDIDATE = "stable_candidate"
    DEFER = "defer"
    REJECT = "reject"
    CONTAMINATED = "contaminated"
    BLOCKED_BY_SOURCE_DIET = "blocked_by_source_diet"
    BLOCKED_BY_OVERLOAD = "blocked_by_overload"
    BLOCKED_BY_DEPRIVATION = "blocked_by_deprivation"
    BLOCKED_BY_OPERATOR_DOMINANCE = "blocked_by_operator_dominance"
    BLOCKED_BY_HUMAN_LABEL = "blocked_by_human_label_dependence"
    BLOCKED_BY_DEBUG_GLOSS = "blocked_by_debug_gloss_dependence"
    BLOCKED_BY_FORBIDDEN_SOURCE = "blocked_by_forbidden_source"
    INCONCLUSIVE = "inconclusive"

    ALL = (BORN, STABLE_CANDIDATE, DEFER, REJECT, CONTAMINATED,
           BLOCKED_BY_SOURCE_DIET, BLOCKED_BY_OVERLOAD, BLOCKED_BY_DEPRIVATION,
           BLOCKED_BY_OPERATOR_DOMINANCE, BLOCKED_BY_HUMAN_LABEL,
           BLOCKED_BY_DEBUG_GLOSS, BLOCKED_BY_FORBIDDEN_SOURCE, INCONCLUSIVE)


@dataclass
class ConceptBirthBlocker:
    """One reason a candidate may not be born (with a correction)."""

    blocker: str
    detail: str = ""
    correction: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"blocker": self.blocker, "detail": self.detail,
                "correction": self.correction}


@dataclass
class ConceptBirthGateResult:
    """The conservative birth decision for one candidate."""

    candidate_id: str
    status: str = ConceptBirthGateStatus.INCONCLUSIVE
    blockers: List[ConceptBirthBlocker] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    rationale: str = ""

    @property
    def born(self) -> bool:
        return self.status == ConceptBirthGateStatus.BORN

    @property
    def blocked(self) -> bool:
        return self.status.startswith("blocked_by_") or self.status in (
            ConceptBirthGateStatus.CONTAMINATED, ConceptBirthGateStatus.REJECT)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "concept_birth_gate_status": self.status,
            "born": self.born, "blocked": self.blocked,
            "blocker_count": len(self.blockers),
            "blockers": [b.to_dict() for b in self.blockers],
            "warnings": list(self.warnings),
            "rationale": self.rationale,
            "enables_semiogenesis": False, "creates_language": False,
            "claims_understanding": False,
            "note": "the birth gate is conservative; it does not enable "
                    "semiogenesis, create language, or claim understanding; it "
                    "creates only operational proto-concept records",
        }


@dataclass
class LiveConceptBirthGate:
    """Decides, conservatively, whether a candidate may become a proto-concept."""

    min_recurrence: int = 3
    min_stability: float = 0.6
    allow_birth: bool = False

    def evaluate(self, *, candidate, stability_score: float,
                 contamination, governance_passed: bool,
                 birth_certificate_present: bool,
                 observation_stability_blocked: bool,
                 source_diet: Dict[str, Any],
                 load: Dict[str, Any]) -> ConceptBirthGateResult:
        r = ConceptBirthGateResult(candidate_id=candidate.candidate_id)
        block = r.blockers.append

        # Hard prerequisites (each block has a precise status + correction).
        if not governance_passed:
            block(ConceptBirthBlocker(
                "governance_not_passed", "governance missing or unapproved",
                "approve the live governance document"))
            r.status = ConceptBirthGateStatus.INCONCLUSIVE
            return self._finalize(r, "prerequisites not met")
        if not birth_certificate_present:
            block(ConceptBirthBlocker(
                "missing_birth_certificate", "no birth certificate present",
                "run the live birth runtime first"))
            r.status = ConceptBirthGateStatus.INCONCLUSIVE
            return self._finalize(r, "prerequisites not met")
        if observation_stability_blocked:
            block(ConceptBirthBlocker(
                "observation_stability_blocked",
                "the observation stability gate is blocked",
                "resolve the observation blockers before ontogenesis"))
            r.status = ConceptBirthGateStatus.INCONCLUSIVE
            return self._finalize(r, "observation not stable")

        # Contamination (blocks birth outright).
        if contamination.contaminated:
            block(ConceptBirthBlocker(
                "contaminated", "candidate has blocking contamination findings",
                "resolve contamination (labels/gloss/operator/command/private)"))
            for f in contamination.findings:
                if f.contamination_type == "forbidden_source":
                    r.status = ConceptBirthGateStatus.BLOCKED_BY_FORBIDDEN_SOURCE
                    return self._finalize(r, "forbidden source present")
                if f.contamination_type == "operator_pulse_dominance":
                    r.status = \
                        ConceptBirthGateStatus.BLOCKED_BY_OPERATOR_DOMINANCE
                    return self._finalize(r, "operator-pulse dominance")
                if f.contamination_type == "human_label_ground_truth_attempt":
                    r.status = ConceptBirthGateStatus.BLOCKED_BY_HUMAN_LABEL
                    return self._finalize(r, "human-label dependence")
                if f.contamination_type == "debug_gloss_ground_truth_attempt":
                    r.status = ConceptBirthGateStatus.BLOCKED_BY_DEBUG_GLOSS
                    return self._finalize(r, "debug-gloss dependence")
                if f.contamination_type == "source_diet_dominance":
                    r.status = ConceptBirthGateStatus.BLOCKED_BY_SOURCE_DIET
                    return self._finalize(r, "source-diet dominance")
            r.status = ConceptBirthGateStatus.CONTAMINATED
            return self._finalize(r, "contaminated candidate")

        # Severe overload / deprivation blocks birth.
        if load.get("severe_overload"):
            block(ConceptBirthBlocker(
                "severe_overload", "the field is severely overloaded",
                "reduce load before concept birth"))
            r.status = ConceptBirthGateStatus.BLOCKED_BY_OVERLOAD
            return self._finalize(r, "severe overload")
        if load.get("severe_deprivation"):
            block(ConceptBirthBlocker(
                "severe_deprivation", "the field is severely deprived",
                "collect more diverse events before concept birth"))
            r.status = ConceptBirthGateStatus.BLOCKED_BY_DEPRIVATION
            return self._finalize(r, "severe deprivation")

        # Source-diet dominance (even without a contamination finding).
        if source_diet.get("balance") in ("operator_pulse_dominant",
                                          "human_text_dominant"):
            block(ConceptBirthBlocker(
                "source_diet_dominant",
                f"source diet is {source_diet.get('balance')!r}",
                "broaden the source diet; operator pulse is stimulus only"))
            r.status = ConceptBirthGateStatus.BLOCKED_BY_SOURCE_DIET
            return self._finalize(r, "source-diet dominance")

        # Evidence thresholds.
        if candidate.recurrence_count < max(2, self.min_recurrence):
            r.warnings.append("recurrence below threshold")
            r.status = ConceptBirthGateStatus.DEFER
            return self._finalize(r, "insufficient recurrence")
        if candidate.operator_only:
            block(ConceptBirthBlocker(
                "operator_text_only",
                "all support comes from the operator pulse",
                "obtain feature support from a non-operator source"))
            r.status = ConceptBirthGateStatus.BLOCKED_BY_OPERATOR_DOMINANCE
            return self._finalize(r, "operator-text-only support")
        if not self._has_non_human_label_signature(candidate):
            block(ConceptBirthBlocker(
                "no_non_human_label_feature",
                "no non-human-label feature signature present",
                "ground the candidate in a non-human-label feature"))
            r.status = ConceptBirthGateStatus.BLOCKED_BY_HUMAN_LABEL
            return self._finalize(r, "human-label dependence")
        if candidate.counter_count >= candidate.supporting_count:
            r.warnings.append("counterevidence >= supporting evidence")
            r.status = ConceptBirthGateStatus.DEFER
            return self._finalize(r, "counterevidence not outweighed")
        if stability_score < self.min_stability:
            r.warnings.append(
                f"stability {stability_score:.2f} below "
                f"{self.min_stability:.2f}")
            r.status = ConceptBirthGateStatus.STABLE_CANDIDATE \
                if stability_score >= self.min_stability - 0.15 \
                else ConceptBirthGateStatus.DEFER
            return self._finalize(r, "stability below birth threshold")

        # All checks passed: born only if birth is allowed by the profile.
        if not self.allow_birth:
            r.status = ConceptBirthGateStatus.STABLE_CANDIDATE
            return self._finalize(
                r, "stable candidate (candidate-only profile; birth withheld)")
        r.status = ConceptBirthGateStatus.BORN
        return self._finalize(r, "born: conservative evidence thresholds met")

    @staticmethod
    def _has_non_human_label_signature(candidate) -> bool:
        non_human = [s for s in candidate.source_distribution
                     if s not in ("operator_pulse", "local_environment_manual")]
        return bool(non_human)

    @staticmethod
    def _finalize(r: ConceptBirthGateResult, rationale: str
                  ) -> ConceptBirthGateResult:
        r.rationale = rationale
        return r
