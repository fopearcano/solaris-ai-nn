"""Live sign birth gate -- conservative, utility- and evidence-grounded.

:class:`LiveSignBirthGate` decides whether a private sign candidate may be *born*
(recorded as an operational private sign), held as a stable candidate, deferred,
rejected, or blocked. Birth requires valid governance, a birth certificate, an
unblocked observation stability gate, a present live ontogenesis report, a linked
born/stable non-contaminated proto-concept, a private/internal token, sign utility
above threshold, contamination below threshold, no label/gloss/operator dependence,
no forbidden source, and more supporting evidence than counterevidence.

The gate is conservative. It does not enable cognition, language, or action -- it
produces only operational private sign records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class SignBirthGateStatus:
    BORN = "born"
    STABLE_CANDIDATE = "stable_candidate"
    DEFER = "defer"
    REJECT = "reject"
    CONTAMINATED = "contaminated"
    BLOCKED_BY_MISSING_CONCEPT = "blocked_by_missing_concept"
    BLOCKED_BY_WEAK_CONCEPT = "blocked_by_weak_concept"
    BLOCKED_BY_LABEL_DEPENDENCE = "blocked_by_label_dependence"
    BLOCKED_BY_DEBUG_GLOSS_DEPENDENCE = "blocked_by_debug_gloss_dependence"
    BLOCKED_BY_OPERATOR_DEPENDENCE = "blocked_by_operator_dependence"
    BLOCKED_BY_LOW_UTILITY = "blocked_by_low_utility"
    BLOCKED_BY_SOURCE_ARTIFACT = "blocked_by_source_artifact"
    BLOCKED_BY_FORBIDDEN_SOURCE = "blocked_by_forbidden_source"
    BLOCKED_BY_OVERLOAD = "blocked_by_overload"
    BLOCKED_BY_DEPRIVATION = "blocked_by_deprivation"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    INCONCLUSIVE = "inconclusive"

    ALL = (BORN, STABLE_CANDIDATE, DEFER, REJECT, CONTAMINATED,
           BLOCKED_BY_MISSING_CONCEPT, BLOCKED_BY_WEAK_CONCEPT,
           BLOCKED_BY_LABEL_DEPENDENCE, BLOCKED_BY_DEBUG_GLOSS_DEPENDENCE,
           BLOCKED_BY_OPERATOR_DEPENDENCE, BLOCKED_BY_LOW_UTILITY,
           BLOCKED_BY_SOURCE_ARTIFACT, BLOCKED_BY_FORBIDDEN_SOURCE,
           BLOCKED_BY_OVERLOAD, BLOCKED_BY_DEPRIVATION, BLOCKED_BY_SAFETY,
           INCONCLUSIVE)


@dataclass
class SignBirthBlocker:
    """One reason a sign candidate may not be born (with a correction)."""

    blocker: str
    detail: str = ""
    correction: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"blocker": self.blocker, "detail": self.detail,
                "correction": self.correction}


@dataclass
class SignBirthGateResult:
    """The conservative birth decision for one sign candidate."""

    sign_id: str
    status: str = SignBirthGateStatus.INCONCLUSIVE
    blockers: List[SignBirthBlocker] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    rationale: str = ""

    @property
    def born(self) -> bool:
        return self.status == SignBirthGateStatus.BORN

    @property
    def blocked(self) -> bool:
        return self.status.startswith("blocked_by_") or self.status in (
            SignBirthGateStatus.CONTAMINATED, SignBirthGateStatus.REJECT)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_id": self.sign_id,
            "sign_birth_gate_status": self.status,
            "born": self.born, "blocked": self.blocked,
            "blocker_count": len(self.blockers),
            "blockers": [b.to_dict() for b in self.blockers],
            "warnings": list(self.warnings),
            "rationale": self.rationale,
            "enables_cognition": False, "enables_language": False,
            "enables_action": False,
            "note": "the sign birth gate is conservative; it does not enable "
                    "cognition, language, or action; it creates only operational "
                    "private sign records",
        }


@dataclass
class LiveSignBirthGate:
    """Decides, conservatively, whether a candidate may become a private sign."""

    min_utility: float = 0.6
    allow_birth: bool = False

    def evaluate(self, *, candidate, utility_score: float, contamination,
                 governance_passed: bool, birth_certificate_present: bool,
                 observation_stability_blocked: bool,
                 ontogenesis_report_present: bool,
                 linked_concept_eligible: bool,
                 linked_concept_contaminated: bool,
                 load: Dict[str, Any]) -> SignBirthGateResult:
        r = SignBirthGateResult(sign_id=candidate.sign_id)
        block = r.blockers.append

        # Hard prerequisites.
        if not governance_passed:
            block(SignBirthBlocker("governance_not_passed",
                                   "governance missing or unapproved",
                                   "approve the live governance document"))
            return self._final(r, SignBirthGateStatus.INCONCLUSIVE,
                               "prerequisites not met")
        if not birth_certificate_present:
            block(SignBirthBlocker("missing_birth_certificate",
                                   "no birth certificate present",
                                   "run the live birth runtime first"))
            return self._final(r, SignBirthGateStatus.INCONCLUSIVE,
                               "prerequisites not met")
        if observation_stability_blocked:
            block(SignBirthBlocker("observation_stability_blocked",
                                   "the observation stability gate is blocked",
                                   "resolve the observation blockers first"))
            return self._final(r, SignBirthGateStatus.INCONCLUSIVE,
                               "observation not stable")
        if not ontogenesis_report_present:
            block(SignBirthBlocker("missing_ontogenesis_report",
                                   "no live ontogenesis report present",
                                   "run first live ontogenesis first"))
            return self._final(r, SignBirthGateStatus.BLOCKED_BY_MISSING_CONCEPT,
                               "no ontogenesis report")

        # Linked proto-concept must be eligible (born/stable) + uncontaminated.
        if not candidate.linked_concept_ids:
            block(SignBirthBlocker("no_linked_concept",
                                   "sign is not linked to any proto-concept",
                                   "link the sign to a born/stable concept"))
            return self._final(r, SignBirthGateStatus.BLOCKED_BY_MISSING_CONCEPT,
                               "no linked concept")
        if linked_concept_contaminated:
            block(SignBirthBlocker("linked_concept_contaminated",
                                   "the linked proto-concept is contaminated",
                                   "resolve the concept contamination first"))
            return self._final(r, SignBirthGateStatus.CONTAMINATED,
                               "linked concept contaminated")
        if not linked_concept_eligible:
            block(SignBirthBlocker("weak_linked_concept",
                                   "the linked proto-concept is not born/stable",
                                   "stabilize the proto-concept first"))
            return self._final(r, SignBirthGateStatus.BLOCKED_BY_WEAK_CONCEPT,
                               "weak linked concept")

        # Contamination (each maps to a precise blocked status).
        if contamination.contaminated:
            for f in contamination.findings:
                t = f.contamination_type
                if not f.blocks_birth:
                    continue
                if t == "secret_marker" or t == "private_data_leak":
                    return self._final(r, SignBirthGateStatus.BLOCKED_BY_SAFETY,
                                       "secret/private token", block,
                                       "remove the secret/private token")
                if t == "forbidden_source":
                    return self._final(
                        r, SignBirthGateStatus.BLOCKED_BY_FORBIDDEN_SOURCE,
                        "forbidden source", block, "remove the forbidden source")
                if t in ("human_label_copy", "label_ground_truth_dependency"):
                    return self._final(
                        r, SignBirthGateStatus.BLOCKED_BY_LABEL_DEPENDENCE,
                        "label dependence", block,
                        "use a private token, not a human label")
                if t in ("debug_gloss_copy", "gloss_ground_truth_dependency"):
                    return self._final(
                        r, SignBirthGateStatus.BLOCKED_BY_DEBUG_GLOSS_DEPENDENCE,
                        "debug-gloss dependence", block,
                        "do not derive the sign from debug gloss")
                if t in ("operator_phrase_copy", "operator_pulse_dominance"):
                    return self._final(
                        r, SignBirthGateStatus.BLOCKED_BY_OPERATOR_DEPENDENCE,
                        "operator dependence", block,
                        "ground the sign in non-operator evidence")
            return self._final(r, SignBirthGateStatus.CONTAMINATED,
                               "contaminated sign", block,
                               "resolve contamination findings")

        # Source artifact (warning-level contamination) downgrades, not births.
        if contamination.is_source_artifact:
            r.warnings.append("linked concept looks like a source artifact")

        # Load gates.
        if load.get("severe_overload"):
            return self._final(r, SignBirthGateStatus.BLOCKED_BY_OVERLOAD,
                               "severe overload", block,
                               "reduce load before sign birth")
        if load.get("severe_deprivation"):
            return self._final(r, SignBirthGateStatus.BLOCKED_BY_DEPRIVATION,
                               "severe deprivation", block,
                               "collect more evidence before sign birth")

        # Utility threshold.
        if utility_score < self.min_utility:
            r.warnings.append(
                f"utility {utility_score:.2f} below {self.min_utility:.2f}")
            status = (SignBirthGateStatus.STABLE_CANDIDATE
                      if utility_score >= self.min_utility - 0.15
                      else SignBirthGateStatus.BLOCKED_BY_LOW_UTILITY)
            return self._final(r, status, "utility below birth threshold")

        # Evidence balance.
        if candidate.counter_count >= candidate.supporting_count:
            r.warnings.append("counterevidence >= supporting evidence")
            return self._final(r, SignBirthGateStatus.DEFER,
                               "counterevidence not outweighed")

        # All checks passed: born only if the profile allows birth.
        if not self.allow_birth:
            return self._final(
                r, SignBirthGateStatus.STABLE_CANDIDATE,
                "stable candidate (candidate-only profile; birth withheld)")
        return self._final(r, SignBirthGateStatus.BORN,
                           "born: conservative utility + evidence met")

    @staticmethod
    def _final(r: SignBirthGateResult, status: str, rationale: str,
               block=None, correction: str = "") -> SignBirthGateResult:
        r.status = status
        r.rationale = rationale
        if block is not None and correction:
            block(SignBirthBlocker(status, rationale, correction))
        return r
