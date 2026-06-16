"""Abstract builder -- claim-constrained abstracts; never overclaims.

:class:`ScientificAbstractBuilder` produces abstract variants (internal research
summary, technical preprint, README-safe summary, operator brief, negative-result
summary, inconclusive-result summary). Abstracts are claim-constrained: they
include no forbidden claim except as a disclaimer, they state when evidence is
weak, and if no publishable claim exists they generate a negative/inconclusive
abstract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AbstractVariant:
    INTERNAL_RESEARCH_SUMMARY = "internal_research_summary"
    TECHNICAL_PREPRINT = "technical_preprint"
    README_SAFE_SUMMARY = "README_safe_summary"
    OPERATOR_BRIEF = "operator_brief"
    NEGATIVE_RESULT_SUMMARY = "negative_result_summary"
    INCONCLUSIVE_RESULT_SUMMARY = "inconclusive_result_summary"

    ALL = (INTERNAL_RESEARCH_SUMMARY, TECHNICAL_PREPRINT, README_SAFE_SUMMARY,
           OPERATOR_BRIEF, NEGATIVE_RESULT_SUMMARY, INCONCLUSIVE_RESULT_SUMMARY)


_DISCLAIMER = ("This work makes no claim of consciousness, sentience, biological "
               "life, personhood, agency, free will, emotion, feeling, "
               "understanding, self-awareness, or subjective experience.")


@dataclass
class AbstractSafetyResult:
    """Whether a generated abstract is claim-safe."""

    safe: bool
    forbidden_findings: int = 0
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"safe": self.safe, "forbidden_findings": self.forbidden_findings,
                "detail": self.detail}


@dataclass
class ScientificAbstractBuilder:
    """Builds claim-constrained abstracts from supported/weak claims."""

    def build(self, variant: str, *,
              supported_claims: Optional[List[Dict]] = None,
              weak_claims: Optional[List[Dict]] = None,
              inconclusive_claims: Optional[List[Dict]] = None,
              negative_results: Optional[List[Dict]] = None,
              limitations: Optional[List[Dict]] = None,
              ) -> str:
        if variant not in AbstractVariant.ALL:
            variant = AbstractVariant.INTERNAL_RESEARCH_SUMMARY
        supported = supported_claims or []
        weak = weak_claims or []
        inconclusive = inconclusive_claims or []
        negatives = negative_results or []
        lims = limitations or []

        # No publishable claim -> negative/inconclusive abstract.
        if not supported and not weak and variant in (
                AbstractVariant.TECHNICAL_PREPRINT,
                AbstractVariant.README_SAFE_SUMMARY,
                AbstractVariant.INTERNAL_RESEARCH_SUMMARY):
            variant = (AbstractVariant.NEGATIVE_RESULT_SUMMARY if negatives
                       else AbstractVariant.INCONCLUSIVE_RESULT_SUMMARY)

        def claim_line(claims, qualifier=""):
            texts = [c.get("text", "") for c in claims[:4]]
            joined = "; ".join(t for t in texts if t)
            return f"{qualifier}{joined}" if joined else ""

        body: List[str] = []
        if variant == AbstractVariant.NEGATIVE_RESULT_SUMMARY:
            body.append("This report records negative and null results: the "
                        "tested hypotheses were not supported by the current "
                        "evidence.")
            line = claim_line(negatives)
            if line:
                body.append(f"Negative findings: {line}.")
        elif variant == AbstractVariant.INCONCLUSIVE_RESULT_SUMMARY:
            body.append("This report records inconclusive results: the current "
                        "evidence neither supports nor refutes the tested "
                        "hypotheses.")
            line = claim_line(inconclusive)
            if line:
                body.append(f"Inconclusive areas: {line}.")
        else:
            if supported:
                body.append(f"Supported findings: {claim_line(supported)}.")
            if weak:
                body.append("The following are only weakly supported and require "
                            f"further evidence: {claim_line(weak)}.")
            if not supported:
                body.append("No finding reached strong support; results below are "
                            "weak or preliminary.")

        if lims:
            top = "; ".join(l.get("text", "") for l in lims[:3] if l.get("text"))
            if top:
                body.append(f"Key limitations: {top}")

        header = {
            AbstractVariant.INTERNAL_RESEARCH_SUMMARY: "Internal Research Summary",
            AbstractVariant.TECHNICAL_PREPRINT: "Technical Preprint Abstract",
            AbstractVariant.README_SAFE_SUMMARY: "README-Safe Summary",
            AbstractVariant.OPERATOR_BRIEF: "Operator Brief",
            AbstractVariant.NEGATIVE_RESULT_SUMMARY: "Negative-Result Summary",
            AbstractVariant.INCONCLUSIVE_RESULT_SUMMARY:
                "Inconclusive-Result Summary",
        }[variant]

        text = f"{header}. " + " ".join(body) + " " + _DISCLAIMER
        return text.strip()

    def build_all(self, **kwargs) -> Dict[str, str]:
        return {v: self.build(v, **kwargs) for v in AbstractVariant.ALL}

    def check_safety(self, text: str) -> AbstractSafetyResult:
        from .forbidden_claims import ForbiddenClaimDetector

        detector = ForbiddenClaimDetector()
        claims = detector.scan(text)
        asserted = [c for c in claims
                    if c.blocks_publication and not c.is_disclaimer]
        return AbstractSafetyResult(
            safe=not asserted, forbidden_findings=len(asserted),
            detail=("contains an asserted forbidden claim" if asserted
                    else "claim-safe (disclaimers allowed)"))
