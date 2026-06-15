"""Promotion / demotion proposals -- role changes on paper, via ADRs.

A :class:`PromotionProposal` (or :class:`DemotionProposal`) records a proposed
change to a module's role. Promotion does not mean metaphysical importance and
demotion does not mean deletion; both are recommendations that require an ADR and
operator review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PromotionProposal:
    """A proposal to promote a module's role (e.g. experimental -> core)."""

    target_module: str
    from_role: str = "experimental_keep"
    to_role: str = "core_keep"
    reasons: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    requires_adr: bool = True
    operator_review_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "note": "promotion is a role recommendation, not metaphysical "
                        "importance; requires an ADR"}


@dataclass
class DemotionProposal:
    """A proposal to demote a module's role (never deletion)."""

    target_module: str
    from_role: str = "core_keep"
    to_role: str = "experimental_keep"
    reasons: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    requires_adr: bool = True
    operator_review_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__),
                "note": "demotion is a role recommendation, not deletion; "
                        "requires an ADR"}


@dataclass
class ModuleRoleChangePlan:
    """Builds promotion/demotion proposals from evidence."""

    def propose_promotion(self, module_name: str, *,
                          evidence_refs: Optional[List[str]] = None,
                          low_safety_risk: bool = True,
                          high_analyzability: bool = True,
                          stable_integration: bool = True,
                          reproducible_benefit: bool = True,
                          ) -> Optional[PromotionProposal]:
        reasons: List[str] = []
        if reproducible_benefit:
            reasons.append("repeated, reproducible positive evidence")
        if low_safety_risk:
            reasons.append("low safety risk")
        if high_analyzability:
            reasons.append("high analyzability")
        if stable_integration:
            reasons.append("stable integration")
        # Promotion needs the candidate criteria to hold.
        if not (reproducible_benefit and low_safety_risk and stable_integration):
            return None
        return PromotionProposal(target_module=module_name, reasons=reasons,
                                 evidence_refs=list(evidence_refs or []))

    def propose_demotion(self, module_name: str, *,
                         evidence_refs: Optional[List[str]] = None,
                         high_overhead: bool = False, weak_evidence: bool = False,
                         repeated_failure: bool = False,
                         profile_specific_only: bool = False,
                         unstable_results: bool = False,
                         ) -> Optional[DemotionProposal]:
        reasons: List[str] = []
        if high_overhead:
            reasons.append("high overhead")
        if weak_evidence:
            reasons.append("weak evidence")
        if repeated_failure:
            reasons.append("repeated failure")
        if profile_specific_only:
            reasons.append("useful only in a specific profile")
        if unstable_results:
            reasons.append("unstable results")
        if not reasons:
            return None
        return DemotionProposal(target_module=module_name, reasons=reasons,
                                evidence_refs=list(evidence_refs or []))
