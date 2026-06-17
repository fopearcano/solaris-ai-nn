"""Downstream contracts -- what each live module owes the membrane boundary.

:class:`MembraneDownstreamContract` declares the obligations of each live module
(Live Birth, Observation, Ontogenesis, Semiogenesis, Cognition, Scientific Claims,
Research Cycle) toward the Environmental Membrane, and :func:`evaluate_contracts`
grades them against the loaded membrane artifacts and ancestry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class DownstreamContractStatus:
    SATISFIED = "satisfied"
    SATISFIED_WITH_WARNINGS = "satisfied_with_warnings"
    VIOLATED = "violated"
    NOT_APPLICABLE = "not_applicable"
    UNKNOWN = "unknown"

    ALL = (SATISFIED, SATISFIED_WITH_WARNINGS, VIOLATED, NOT_APPLICABLE, UNKNOWN)


@dataclass
class DownstreamContractRequirement:
    """One requirement within a contract."""

    requirement: str
    satisfied: bool = True
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"requirement": self.requirement, "satisfied": self.satisfied,
                "detail": self.detail}


@dataclass
class MembraneDownstreamContract:
    """One module's contract toward the membrane boundary."""

    module: str
    requirements: List[DownstreamContractRequirement] = field(
        default_factory=list)
    status: str = DownstreamContractStatus.UNKNOWN

    def finalize(self) -> "MembraneDownstreamContract":
        unmet = [r for r in self.requirements if not r.satisfied]
        if not self.requirements:
            self.status = DownstreamContractStatus.NOT_APPLICABLE
        elif not unmet:
            self.status = DownstreamContractStatus.SATISFIED
        elif all(r.detail.startswith("warning") for r in unmet):
            self.status = DownstreamContractStatus.SATISFIED_WITH_WARNINGS
        else:
            self.status = DownstreamContractStatus.VIOLATED
        return self

    def to_dict(self) -> Dict[str, Any]:
        return {"module": self.module, "status": self.status,
                "requirements": [r.to_dict() for r in self.requirements]}


def _contract(module: str, reqs: List[DownstreamContractRequirement],
              ) -> MembraneDownstreamContract:
    return MembraneDownstreamContract(module=module,
                                      requirements=reqs).finalize()


def evaluate_contracts(*, membrane_present: bool, impressions_present: bool,
                       ancestry, strict: bool) -> List[MembraneDownstreamContract]:
    """Grade all downstream contracts against the loaded artifacts."""
    R = DownstreamContractRequirement
    with_anc = ancestry.with_impression_ancestry if ancestry else 0
    missing = ancestry.missing_ancestry if ancestry else 0

    birth = _contract("live_birth", [
        R("validates and quarantines events", True),
        R("hands accepted events to the membrane", membrane_present,
          "" if membrane_present else "membrane not present"),
        R("does not send accepted events directly to learning modules", True)])

    observation = _contract("live_observation", [
        R("may inspect raw events for diagnostics", True),
        R("uses sensory impressions for impression diet / salience / pressure",
          impressions_present,
          "" if impressions_present else "no impressions to consume")])

    onto_ok = impressions_present or not membrane_present
    ontogenesis = _contract("live_ontogenesis", [
        R("forms proto-concepts from sensory impressions when available",
          onto_ok, "" if onto_ok else (
              "raw fallback in strict live mode" if strict
              else "warning: raw fallback used")),
        R("raw-event fallback is explicit (blocked in strict live mode)",
          impressions_present or not strict,
          "" if (impressions_present or not strict) else
          "raw fallback blocked in strict mode")])

    sign_ok = (not membrane_present) or with_anc > 0 or missing == 0
    semiogenesis = _contract("live_semiogenesis", [
        R("forms signs from concepts with impression ancestry", sign_ok,
          "" if sign_ok else (
              "missing impression ancestry" if strict
              else "warning: some signs lack impression ancestry")),
        R("contaminated impression ancestry downgrades/blocks sign birth",
          True)])

    cognition = _contract("live_cognition", [
        R("forms traces from signs with impression ancestry", sign_ok,
          "" if sign_ok else (
              "missing impression ancestry" if strict
              else "warning: some traces lack impression ancestry")),
        R("prediction assessment distinguishes event vs impression prediction",
          True)])

    claims = _contract("scientific_claims", [
        R("distinguishes raw event evidence from membrane-filtered evidence",
          True),
        R("blocks claims when modules bypass membrane without justification",
          membrane_present or not strict,
          "" if (membrane_present or not strict) else
          "membrane bypass without justification")])

    research = _contract("research_cycle", [
        R("treats membrane bypass as blocker or warning", True)])

    return [birth, observation, ontogenesis, semiogenesis, cognition, claims,
            research]


def summary(contracts: List[MembraneDownstreamContract]) -> Dict[str, Any]:
    statuses: Dict[str, int] = {}
    for c in contracts:
        statuses[c.status] = statuses.get(c.status, 0) + 1
    return {
        "contract_count": len(contracts),
        "by_status": statuses,
        "violated_count": statuses.get(DownstreamContractStatus.VIOLATED, 0),
        "contracts": [c.to_dict() for c in contracts],
        "note": "downstream modules should consume membrane-filtered sensory "
                "impressions; contracts grade that obligation",
    }
