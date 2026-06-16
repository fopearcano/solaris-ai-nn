"""Research cycle blocked states -- detected blockers + advisory resolutions.

:class:`BlockedStateResolver` detects why a cycle is blocked and recommends a
resolution. The resolver recommends only -- it executes nothing -- and a critical
safety blocker can never be bypassed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class BlockedReason:
    MISSING_BASELINE = "missing_baseline"
    INVALID_BASELINE = "invalid_baseline"
    SAFETY_GATE_FAILED = "safety_gate_failed"
    MISSING_ARCHITECTURE_EVIDENCE = "missing_architecture_evidence"
    FALSIFIED_PROPOSAL = "falsified_proposal"
    EXPERIMENT_PACK_UNSAFE = "experiment_pack_unsafe"
    IMPLEMENTATION_MISSING = "implementation_missing"
    IMPLEMENTATION_FAILED_AUDIT = "implementation_failed_audit"
    TESTS_FAILED = "tests_failed"
    CLAIMGUARD_FAILED = "claimguard_failed"
    HUMAN_MERGE_MISSING = "human_merge_missing"
    POST_MERGE_EVIDENCE_MISSING = "post_merge_evidence_missing"
    REGRESSION_DETECTED = "regression_detected"
    CRITICAL_LIMITATION = "critical_limitation"
    OPERATOR_REJECTION = "operator_rejection"
    UNKNOWN = "unknown"

    ALL = (MISSING_BASELINE, INVALID_BASELINE, SAFETY_GATE_FAILED,
           MISSING_ARCHITECTURE_EVIDENCE, FALSIFIED_PROPOSAL,
           EXPERIMENT_PACK_UNSAFE, IMPLEMENTATION_MISSING,
           IMPLEMENTATION_FAILED_AUDIT, TESTS_FAILED, CLAIMGUARD_FAILED,
           HUMAN_MERGE_MISSING, POST_MERGE_EVIDENCE_MISSING, REGRESSION_DETECTED,
           CRITICAL_LIMITATION, OPERATOR_REJECTION, UNKNOWN)

    CRITICAL_SAFETY = (SAFETY_GATE_FAILED, EXPERIMENT_PACK_UNSAFE,
                       CLAIMGUARD_FAILED, CRITICAL_LIMITATION)


class ResolverRecommendation:
    COLLECT_MISSING_EVIDENCE = "collect_missing_evidence"
    RUN_SAFETY_AUDIT = "run_safety_audit"
    REVISE_EXPERIMENT_PACK = "revise_experiment_pack"
    REQUEST_IMPLEMENTATION_ARTIFACT = "request_implementation_artifact"
    REQUEST_OPERATOR_DECISION = "request_operator_decision"
    RUN_IMPLEMENTATION_INTAKE = "run_implementation_intake"
    RUN_POST_MERGE_ASSIMILATION = "run_post_merge_assimilation"
    ROLLBACK_REVIEW = "rollback_review"
    ARCHIVE_CYCLE = "archive_cycle"
    RESTART_FROM_BASELINE = "restart_from_baseline"
    INCONCLUSIVE = "inconclusive"

    ALL = (COLLECT_MISSING_EVIDENCE, RUN_SAFETY_AUDIT, REVISE_EXPERIMENT_PACK,
           REQUEST_IMPLEMENTATION_ARTIFACT, REQUEST_OPERATOR_DECISION,
           RUN_IMPLEMENTATION_INTAKE, RUN_POST_MERGE_ASSIMILATION,
           ROLLBACK_REVIEW, ARCHIVE_CYCLE, RESTART_FROM_BASELINE, INCONCLUSIVE)


@dataclass
class ResearchCycleBlockedState:
    """One detected blocker + its advisory resolution recommendation."""

    reason: str
    recommendation: str
    critical_safety: bool = False
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"reason": self.reason, "recommendation": self.recommendation,
                "critical_safety": self.critical_safety, "detail": self.detail,
                "can_bypass": False if self.critical_safety else None,
                "executed": False}


# reason -> advisory resolution.
_RESOLUTION = {
    BlockedReason.MISSING_BASELINE: ResolverRecommendation.RESTART_FROM_BASELINE,
    BlockedReason.INVALID_BASELINE: ResolverRecommendation.RESTART_FROM_BASELINE,
    BlockedReason.SAFETY_GATE_FAILED: ResolverRecommendation.RUN_SAFETY_AUDIT,
    BlockedReason.MISSING_ARCHITECTURE_EVIDENCE:
        ResolverRecommendation.COLLECT_MISSING_EVIDENCE,
    BlockedReason.FALSIFIED_PROPOSAL: ResolverRecommendation.REVISE_EXPERIMENT_PACK,
    BlockedReason.EXPERIMENT_PACK_UNSAFE:
        ResolverRecommendation.REVISE_EXPERIMENT_PACK,
    BlockedReason.IMPLEMENTATION_MISSING:
        ResolverRecommendation.REQUEST_IMPLEMENTATION_ARTIFACT,
    BlockedReason.IMPLEMENTATION_FAILED_AUDIT:
        ResolverRecommendation.REVISE_EXPERIMENT_PACK,
    BlockedReason.TESTS_FAILED: ResolverRecommendation.REVISE_EXPERIMENT_PACK,
    BlockedReason.CLAIMGUARD_FAILED: ResolverRecommendation.RUN_SAFETY_AUDIT,
    BlockedReason.HUMAN_MERGE_MISSING:
        ResolverRecommendation.REQUEST_OPERATOR_DECISION,
    BlockedReason.POST_MERGE_EVIDENCE_MISSING:
        ResolverRecommendation.RUN_POST_MERGE_ASSIMILATION,
    BlockedReason.REGRESSION_DETECTED: ResolverRecommendation.ROLLBACK_REVIEW,
    BlockedReason.CRITICAL_LIMITATION:
        ResolverRecommendation.COLLECT_MISSING_EVIDENCE,
    BlockedReason.OPERATOR_REJECTION: ResolverRecommendation.ARCHIVE_CYCLE,
    BlockedReason.UNKNOWN: ResolverRecommendation.INCONCLUSIVE,
}


@dataclass
class BlockedStateResolver:
    """Detects blockers and recommends resolutions (recommend-only)."""

    def detect(self, bundle: Dict[str, Any], *,
               operator_decisions: Optional[List[Dict]] = None,
               ) -> List[ResearchCycleBlockedState]:
        bundle = bundle or {}
        intake = bundle.get("implementation_intake", {}) or {}
        pm = bundle.get("post_merge", {}) or {}
        rb = bundle.get("research_baseline", {}) or {}
        fals = bundle.get("falsification", {}) or {}
        comp = bundle.get("experiment_compiler", {}) or {}
        out: List[ResearchCycleBlockedState] = []

        def add(reason: str, detail: str = "") -> None:
            out.append(ResearchCycleBlockedState(
                reason=reason, recommendation=_RESOLUTION.get(
                    reason, ResolverRecommendation.INCONCLUSIVE),
                critical_safety=reason in BlockedReason.CRITICAL_SAFETY,
                detail=detail))

        if str(intake.get("merge_recommendation_status", "")).startswith(
                "block_merge_due_to_safety") or \
                int(intake.get("critical_safety_regression_count", 0) or 0) > 0:
            add(BlockedReason.SAFETY_GATE_FAILED,
                "implementation intake reports a critical safety issue")
        if str(intake.get("merge_recommendation_status", "")).startswith(
                "block_merge_due_to_tests"):
            add(BlockedReason.TESTS_FAILED, "intake reports failing tests")
        if comp.get("safety_gate_failure_count", 0) and \
                comp.get("ready_spec_count", 0) == 0:
            add(BlockedReason.EXPERIMENT_PACK_UNSAFE,
                "experiment pack failed a critical safety gate")
        if int(fals.get("falsified_claim_count", 0) or 0) > 0:
            add(BlockedReason.FALSIFIED_PROPOSAL,
                "a core claim was falsified")
        if int(pm.get("critical_regression_count", 0) or 0) > 0:
            add(BlockedReason.REGRESSION_DETECTED,
                "post-merge critical regression")
        if rb.get("baseline_status") == "blocked" or \
                int(rb.get("critical_limitation_count", 0) or 0) > 0:
            add(BlockedReason.CRITICAL_LIMITATION,
                "research baseline has a critical limitation")
        for d in (operator_decisions or []):
            if d.get("status") == "rejected":
                add(BlockedReason.OPERATOR_REJECTION,
                    f"operator rejected: {d.get('decision_type')}")
                break
        return out

    @staticmethod
    def summary(states: List[ResearchCycleBlockedState]) -> Dict[str, Any]:
        critical = [s for s in states if s.critical_safety]
        return {
            "blocked_state_count": len(states),
            "unresolved_blocker_count": len(states),
            "critical_safety_blocker_count": len(critical),
            "states": [s.to_dict() for s in states],
            "note": "the resolver recommends only and executes nothing; a "
                    "critical safety blocker can never be bypassed",
        }
