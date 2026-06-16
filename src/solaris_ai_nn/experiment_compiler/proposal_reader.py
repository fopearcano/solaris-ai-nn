"""Architecture proposal reader -- normalize proposals into compilable form.

:class:`ArchitectureProposalReader` reads variant proposals, ablation plans,
promotion decisions, freeze/retirement proposals, branch manifests, and
experiment-queue items (as dicts), and extracts the fields the compiler needs:
target modules, proposed changes, expected effects, risks, evidence refs,
falsification requirements, safety constraints, success/failure/rollback
criteria, and missing evidence. Unsafe proposals become *blocked* read results;
inconclusive proposals become *retest* read results -- never implementation packs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ProposalPriority:
    P0 = "p0"
    P1 = "p1"
    P2 = "p2"
    P3 = "p3"

    ALL = (P0, P1, P2, P3)


class ProposalDisposition:
    IMPLEMENTABLE = "implementable"
    BLOCKED_UNSAFE = "blocked_unsafe"
    BLOCKED_FALSIFIED = "blocked_falsified"
    RETEST_INCONCLUSIVE = "retest_inconclusive"

    ALL = (IMPLEMENTABLE, BLOCKED_UNSAFE, BLOCKED_FALSIFIED,
           RETEST_INCONCLUSIVE)


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


@dataclass
class ProposalReadResult:
    """Normalized, disposition-tagged view of one architecture proposal."""

    proposal_id: str
    target_modules: List[str] = field(default_factory=list)
    proposed_changes: List[str] = field(default_factory=list)
    expected_effects: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    falsification_requirements: List[str] = field(default_factory=list)
    safety_constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    failure_criteria: List[str] = field(default_factory=list)
    rollback_criteria: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    priority: str = ProposalPriority.P2
    disposition: str = ProposalDisposition.IMPLEMENTABLE
    target_label: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "target_modules": list(self.target_modules),
            "proposed_changes": list(self.proposed_changes),
            "expected_effects": list(self.expected_effects),
            "risks": list(self.risks),
            "evidence_refs": list(self.evidence_refs),
            "falsification_requirements": list(self.falsification_requirements),
            "safety_constraints": list(self.safety_constraints),
            "success_criteria": list(self.success_criteria),
            "failure_criteria": list(self.failure_criteria),
            "rollback_criteria": list(self.rollback_criteria),
            "missing_evidence": list(self.missing_evidence),
            "priority": self.priority, "disposition": self.disposition,
            "target_label": self.target_label,
        }


@dataclass
class ArchitectureProposalReader:
    """Normalizes proposal dicts and tags each with a compile disposition."""

    def read(self, proposal: Dict[str, Any], *,
             index: int = 0) -> ProposalReadResult:
        pid = str(proposal.get("proposal_id")
                  or proposal.get("id")
                  or f"proposal_{index}")
        target_label = str(proposal.get("target")
                           or proposal.get("target_label") or "unspecified")
        modules = _as_list(proposal.get("target_modules")) or (
            [target_label] if target_label != "unspecified" else [])
        result = ProposalReadResult(
            proposal_id=pid, target_label=target_label,
            target_modules=[str(m) for m in modules],
            proposed_changes=_as_list(proposal.get("proposed_changes")
                                      or proposal.get("proposal")),
            expected_effects=_as_list(proposal.get("expected_effects")
                                      or proposal.get("reason")),
            risks=_as_list(proposal.get("risks")),
            evidence_refs=_as_list(proposal.get("evidence_refs")),
            falsification_requirements=_as_list(
                proposal.get("falsification_requirements")),
            safety_constraints=_as_list(proposal.get("safety_constraints")),
            success_criteria=_as_list(proposal.get("success_criteria")),
            failure_criteria=_as_list(proposal.get("failure_criteria")),
            rollback_criteria=_as_list(proposal.get("rollback_criteria")),
            missing_evidence=_as_list(proposal.get("missing_evidence")),
            priority=str(proposal.get("priority", ProposalPriority.P2)),
            raw=dict(proposal))
        result.disposition = self._disposition(proposal, result)
        return result

    @staticmethod
    def _disposition(proposal: Dict[str, Any],
                     result: ProposalReadResult) -> str:
        # Unsafe proposals never become implementation packs.
        if proposal.get("safe") is False or proposal.get("unsafe") is True:
            return ProposalDisposition.BLOCKED_UNSAFE
        # Falsified evidence blocks promotion/implementation.
        if proposal.get("blocks_promotion") or proposal.get("falsified"):
            return ProposalDisposition.BLOCKED_FALSIFIED
        # Inconclusive / missing-evidence proposals need a retest, not a pack.
        if proposal.get("inconclusive") or result.missing_evidence \
                or proposal.get("disposition") == "inconclusive":
            return ProposalDisposition.RETEST_INCONCLUSIVE
        return ProposalDisposition.IMPLEMENTABLE

    def read_all(self, proposals: List[Dict[str, Any]],
                 ) -> List[ProposalReadResult]:
        return [self.read(p, index=i) for i, p in enumerate(proposals or [])]
