"""Pruning proposals -- a plan to remove, never an act of removal.

The :class:`PruningProposalBuilder` produces a :class:`PruningProposal` for a
module: its reason, evidence, impacts, fallback/compatibility/test/rollback
plans, and operator-review requirement. It never deletes code, never edits
imports, and never proposes pruning a safety-critical module (it may suggest
quarantine first). Pruning is a plan, not an action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class PruningImplementationStatus:
    PLANNING_ONLY = "planning_only"
    EXTERNAL_MANUAL_CHANGE_REQUIRED = "external_manual_change_required"
    NOT_IMPLEMENTED = "not_implemented"

    ALL = (PLANNING_ONLY, EXTERNAL_MANUAL_CHANGE_REQUIRED, NOT_IMPLEMENTED)


@dataclass
class PruningRisk:
    integration_impact: str = "unknown"
    safety_impact: str = "none"
    severity: str = "moderate"

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PruningPlan:
    fallback_plan: str = ""
    compatibility_plan: str = ""
    test_plan: str = ""
    rollback_plan: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class PruningProposal:
    """A planning-only proposal to remove (or quarantine) a module."""

    target_module: str
    reason: str
    quarantine_first: bool = False
    blocked: bool = False
    blocked_reason: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    expected_benefit: str = ""
    risk: PruningRisk = field(default_factory=PruningRisk)
    plan: PruningPlan = field(default_factory=PruningPlan)
    operator_review_required: bool = True
    implementation_status: str = PruningImplementationStatus.PLANNING_ONLY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_module": self.target_module, "reason": self.reason,
            "quarantine_first": self.quarantine_first, "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
            "evidence_refs": self.evidence_refs,
            "expected_benefit": self.expected_benefit,
            "risk": self.risk.to_dict(), "plan": self.plan.to_dict(),
            "operator_review_required": True,
            "implementation_status": self.implementation_status,
            "note": "pruning is a plan only; no code is deleted and no import "
                    "is edited",
        }


@dataclass
class PruningProposalBuilder:
    """Builds pruning proposals; never prunes safety-critical modules."""

    def build(self, target_module: str, *, safety_critical: bool = False,
              reason: str = "", evidence_refs: Optional[List[str]] = None,
              integration_count: int = 0, failure_rate: float = 0.0,
              ) -> PruningProposal:
        evidence_refs = list(evidence_refs or [])
        if safety_critical:
            return PruningProposal(
                target_module=target_module,
                reason=reason or "performance evidence",
                blocked=True,
                blocked_reason="safety-critical modules cannot be pruned on "
                               "performance evidence alone",
                evidence_refs=evidence_refs,
                implementation_status=PruningImplementationStatus.NOT_IMPLEMENTED)
        quarantine_first = failure_rate >= 0.5 or integration_count >= 3
        risk = PruningRisk(
            integration_impact=("high" if integration_count >= 3
                                else "moderate" if integration_count >= 1
                                else "low"),
            safety_impact="none",
            severity="high" if integration_count >= 3 else "moderate")
        plan = PruningPlan(
            fallback_plan="keep the module behind a disabled toggle first",
            compatibility_plan="confirm no profile requires the module; update "
                               "the module registry and scenario profiles",
            test_plan="run the research ablation that removes the module and "
                      "the full test suite",
            rollback_plan="re-enable the module toggle; restore the registry "
                          "entry")
        return PruningProposal(
            target_module=target_module,
            reason=reason or "weak/negative research evidence in this profile",
            quarantine_first=quarantine_first, evidence_refs=evidence_refs,
            expected_benefit="reduced complexity and overhead if the module is "
                             "dead weight",
            risk=risk, plan=plan,
            implementation_status=PruningImplementationStatus
            .EXTERNAL_MANUAL_CHANGE_REQUIRED)

    def build_from_assessment(self, assessment: Any,
                              safety_critical: bool = False) -> PruningProposal:
        return self.build(
            assessment.module_name,
            safety_critical=safety_critical or getattr(assessment,
                                                       "safety_critical", False),
            reason="; ".join(getattr(assessment, "rationale", [])),
            evidence_refs=list(getattr(assessment, "evidence_refs", [])))
