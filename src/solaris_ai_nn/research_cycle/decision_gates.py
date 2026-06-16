"""Research cycle decision gates -- advisory checks, never self-approving.

:class:`ResearchCycleDecisionGate` evaluates the gates between cycle stages
(baseline validation, roadmap readiness, architecture evidence, experiment-pack
safety, implementation intake, merge readiness, post-merge validation, research
baseline, soak/replication/falsification readiness, next-cycle). Safety failures
block gates; falsified core claims block promotion gates; missing critical
evidence blocks gates; operator-decision gates cannot be auto-approved; and gate
results are advisory metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DecisionGateType:
    BASELINE_VALIDATION = "baseline_validation_gate"
    ROADMAP_READINESS = "roadmap_readiness_gate"
    ARCHITECTURE_EVIDENCE = "architecture_evidence_gate"
    EXPERIMENT_PACK_SAFETY = "experiment_pack_safety_gate"
    IMPLEMENTATION_INTAKE = "implementation_intake_gate"
    MERGE_READINESS = "merge_readiness_gate"
    POST_MERGE_VALIDATION = "post_merge_validation_gate"
    RESEARCH_BASELINE = "research_baseline_gate"
    SOAK_READINESS = "soak_readiness_gate"
    REPLICATION_READINESS = "replication_readiness_gate"
    FALSIFICATION_READINESS = "falsification_readiness_gate"
    NEXT_CYCLE = "next_cycle_gate"

    ALL = (BASELINE_VALIDATION, ROADMAP_READINESS, ARCHITECTURE_EVIDENCE,
           EXPERIMENT_PACK_SAFETY, IMPLEMENTATION_INTAKE, MERGE_READINESS,
           POST_MERGE_VALIDATION, RESEARCH_BASELINE, SOAK_READINESS,
           REPLICATION_READINESS, FALSIFICATION_READINESS, NEXT_CYCLE)

    # Gates that promote the project forward (falsified core claims block these).
    PROMOTION_GATES = (RESEARCH_BASELINE, NEXT_CYCLE, MERGE_READINESS)
    # Gates that require an explicit operator decision.
    OPERATOR_GATES = (MERGE_READINESS, RESEARCH_BASELINE, NEXT_CYCLE)


class DecisionGateStatus:
    PASS = "pass"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    BLOCKED_BY_FALSIFICATION = "blocked_by_falsification"
    BLOCKED_BY_MISSING_EVIDENCE = "blocked_by_missing_evidence"
    BLOCKED_BY_REGRESSION = "blocked_by_regression"
    WAITING_FOR_OPERATOR = "waiting_for_operator"
    NOT_APPLICABLE = "not_applicable"
    INCONCLUSIVE = "inconclusive"

    ALL = (PASS, BLOCKED_BY_SAFETY, BLOCKED_BY_FALSIFICATION,
           BLOCKED_BY_MISSING_EVIDENCE, BLOCKED_BY_REGRESSION,
           WAITING_FOR_OPERATOR, NOT_APPLICABLE, INCONCLUSIVE)

    PASSED = (PASS, NOT_APPLICABLE)


@dataclass
class DecisionGateResult:
    """The advisory result of evaluating one gate."""

    gate_type: str
    status: str
    missing_evidence: List[str] = field(default_factory=list)
    operator_decision_required: bool = False
    detail: str = ""

    @property
    def passed(self) -> bool:
        return self.status in DecisionGateStatus.PASSED

    @property
    def blocked(self) -> bool:
        return self.status in (DecisionGateStatus.BLOCKED_BY_SAFETY,
                               DecisionGateStatus.BLOCKED_BY_FALSIFICATION,
                               DecisionGateStatus.BLOCKED_BY_MISSING_EVIDENCE,
                               DecisionGateStatus.BLOCKED_BY_REGRESSION)

    def to_dict(self) -> Dict[str, Any]:
        return {"gate_type": self.gate_type, "status": self.status,
                "passed": self.passed, "blocked": self.blocked,
                "missing_evidence": list(self.missing_evidence),
                "operator_decision_required": self.operator_decision_required,
                "detail": self.detail, "advisory": True}


@dataclass
class ResearchCycleDecisionGate:
    """Evaluates the cycle decision gates from the evidence bundle."""

    def evaluate_all(self, bundle: Dict[str, Any], *,
                     operator_decisions: Optional[List[Dict]] = None,
                     ) -> List[DecisionGateResult]:
        bundle = bundle or {}
        made = {d.get("decision_type"): d.get("status")
                for d in (operator_decisions or [])}
        return [self._evaluate(g, bundle, made) for g in DecisionGateType.ALL]

    def _evaluate(self, gate: str, bundle: Dict[str, Any],
                  made: Dict[str, Any]) -> DecisionGateResult:
        rb = bundle.get("research_baseline", {}) or {}
        pm = bundle.get("post_merge", {}) or {}
        intake = bundle.get("implementation_intake", {}) or {}
        compiler = bundle.get("experiment_compiler", {}) or {}
        arch = bundle.get("architecture_evolution", {}) or {}
        fals = bundle.get("falsification", {}) or {}

        # Global safety check applies to every promotion gate.
        safety_failed = self._safety_failed(bundle)
        falsified = int(fals.get("falsified_claim_count", 0) or 0) > 0
        regressed = int(pm.get("critical_regression_count", 0) or 0) > 0

        if gate in DecisionGateType.PROMOTION_GATES:
            if safety_failed:
                return DecisionGateResult(
                    gate, DecisionGateStatus.BLOCKED_BY_SAFETY,
                    detail="a critical safety failure blocks this promotion gate")
            if falsified:
                return DecisionGateResult(
                    gate, DecisionGateStatus.BLOCKED_BY_FALSIFICATION,
                    detail="a falsified core claim blocks this promotion gate")
            if regressed:
                return DecisionGateResult(
                    gate, DecisionGateStatus.BLOCKED_BY_REGRESSION,
                    detail="a critical regression blocks this promotion gate")

        # Operator-decision gates cannot be auto-approved.
        if gate in DecisionGateType.OPERATOR_GATES:
            req_decision = self._required_decision(gate)
            if made.get(req_decision) != "approved":
                # Only "waiting" if the upstream evidence exists at all.
                if self._gate_evidence_present(gate, bundle):
                    return DecisionGateResult(
                        gate, DecisionGateStatus.WAITING_FOR_OPERATOR,
                        operator_decision_required=True,
                        detail=f"requires operator decision: {req_decision}")

        # Per-gate evidence checks.
        missing = self._missing_for(gate, bundle)
        if missing:
            return DecisionGateResult(
                gate, DecisionGateStatus.BLOCKED_BY_MISSING_EVIDENCE,
                missing_evidence=missing,
                detail=f"missing required evidence: {missing}")
        if not self._gate_evidence_present(gate, bundle):
            return DecisionGateResult(gate, DecisionGateStatus.NOT_APPLICABLE,
                                      detail="upstream evidence not yet present")
        return DecisionGateResult(gate, DecisionGateStatus.PASS)

    @staticmethod
    def _safety_failed(bundle: Dict[str, Any]) -> bool:
        rb = bundle.get("research_baseline", {}) or {}
        intake = bundle.get("implementation_intake", {}) or {}
        pm = bundle.get("post_merge", {}) or {}
        return (rb.get("safety_boundary_status") == "boundary_failed"
                or int(intake.get("critical_safety_regression_count", 0)
                       or 0) > 0
                or str(intake.get("merge_recommendation_status", "")).startswith(
                    "block_merge_due_to_safety")
                or str(pm.get("candidate_baseline_status", "")) ==
                "blocked_by_safety")

    @staticmethod
    def _required_decision(gate: str) -> str:
        from .operator_decisions import OperatorDecisionType

        return {
            DecisionGateType.MERGE_READINESS:
                OperatorDecisionType.CONFIRM_EXTERNAL_MERGE,
            DecisionGateType.RESEARCH_BASELINE:
                OperatorDecisionType.APPROVE_CANDIDATE_BASELINE,
            DecisionGateType.NEXT_CYCLE:
                OperatorDecisionType.START_NEXT_CYCLE,
        }.get(gate, "")

    @staticmethod
    def _gate_evidence_present(gate: str, bundle: Dict[str, Any]) -> bool:
        return {
            DecisionGateType.BASELINE_VALIDATION: bool(
                bundle.get("research_baseline")),
            DecisionGateType.ROADMAP_READINESS: bool(bundle.get("roadmap")),
            DecisionGateType.ARCHITECTURE_EVIDENCE: bool(
                bundle.get("architecture_evolution")),
            DecisionGateType.EXPERIMENT_PACK_SAFETY: bool(
                bundle.get("experiment_compiler")),
            DecisionGateType.IMPLEMENTATION_INTAKE: bool(
                bundle.get("implementation_intake")),
            DecisionGateType.MERGE_READINESS: bool(
                bundle.get("implementation_intake")),
            DecisionGateType.POST_MERGE_VALIDATION: bool(
                bundle.get("post_merge")),
            DecisionGateType.RESEARCH_BASELINE: bool(
                bundle.get("post_merge") or bundle.get("research_baseline")),
            DecisionGateType.SOAK_READINESS: bool(
                bundle.get("research_baseline")),
            DecisionGateType.REPLICATION_READINESS: bool(
                bundle.get("research_baseline")),
            DecisionGateType.FALSIFICATION_READINESS: bool(
                bundle.get("research_baseline")),
            DecisionGateType.NEXT_CYCLE: bool(bundle.get("research_baseline")),
        }.get(gate, False)

    @staticmethod
    def _missing_for(gate: str, bundle: Dict[str, Any]) -> List[str]:
        # Experiment-pack safety gate requires the compiler's safety gates.
        if gate == DecisionGateType.EXPERIMENT_PACK_SAFETY and \
                bundle.get("experiment_compiler"):
            comp = bundle["experiment_compiler"]
            if comp.get("safety_gate_failure_count", 0) and \
                    comp.get("ready_spec_count", 0) == 0:
                return ["experiment_pack_safety_gates"]
        return []

    @staticmethod
    def summary(results: List[DecisionGateResult]) -> Dict[str, Any]:
        failed = [r for r in results if r.blocked]
        waiting = [r for r in results
                   if r.status == DecisionGateStatus.WAITING_FOR_OPERATOR]
        return {
            "decision_gate_count": len(results),
            "passed_count": sum(1 for r in results if r.passed),
            "failed_decision_gate_count": len(failed),
            "waiting_for_operator_count": len(waiting),
            "failed_gates": [r.gate_type for r in failed],
            "results": [r.to_dict() for r in results],
            "all_critical_passed": not failed,
        }
