"""Safety failure triage -- classify a failure and recommend a safe response.

The :class:`SafetyFailureTriage` classifies a safety failure (boundary leak,
missing evidence, critical invariant failure, ...) and recommends a *safe*
response (block the profile, return to safe mode, revise the firewall, archive
and stop, ...). It never repairs automatically; missing evidence is never
treated as safe; a fatal boundary leak recommends archive-and-stop / block.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SafetyFailureClass:
    BOUNDARY_LEAK = "boundary_leak"
    MISSING_EVIDENCE = "missing_evidence"
    CRITICAL_INVARIANT_FAILURE = "critical_invariant_failure"
    GOVERNANCE_GAP = "governance_gap"
    FIREWALL_GAP = "firewall_gap"
    CLAIM_SAFETY_GAP = "claim_safety_gap"
    SOURCE_BOUNDARY_GAP = "source_boundary_gap"
    SIMULATION_REAL_CONFUSION = "simulation_real_confusion"
    ORCHESTRATOR_BYPASS = "orchestrator_bypass"
    UNKNOWN = "unknown"

    ALL = (BOUNDARY_LEAK, MISSING_EVIDENCE, CRITICAL_INVARIANT_FAILURE,
           GOVERNANCE_GAP, FIREWALL_GAP, CLAIM_SAFETY_GAP, SOURCE_BOUNDARY_GAP,
           SIMULATION_REAL_CONFUSION, ORCHESTRATOR_BYPASS, UNKNOWN)


class SafetyRecommendedAction:
    BLOCK_PROFILE = "block_profile"
    DISABLE_MODULE = "disable_module"
    RETURN_TO_SAFE_MODE = "return_to_safe_mode"
    REVISE_FIREWALL = "revise_firewall"
    REVISE_GOVERNANCE = "revise_governance"
    REVISE_CLAIM_GUARD = "revise_claim_guard"
    RERUN_RED_TEAM = "rerun_red_team"
    ARCHIVE_AND_STOP = "archive_and_stop"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"

    ALL = (BLOCK_PROFILE, DISABLE_MODULE, RETURN_TO_SAFE_MODE, REVISE_FIREWALL,
           REVISE_GOVERNANCE, REVISE_CLAIM_GUARD, RERUN_RED_TEAM,
           ARCHIVE_AND_STOP, MANUAL_REVIEW_REQUIRED)


# Category -> (failure class, recommended action) for classification.
_CATEGORY_MAP = {
    "no_real_world_actuation": (SafetyFailureClass.FIREWALL_GAP,
                                SafetyRecommendedAction.ARCHIVE_AND_STOP),
    "simulation_only_motor_boundary": (SafetyFailureClass.FIREWALL_GAP,
                                       SafetyRecommendedAction.REVISE_FIREWALL),
    "no_external_authority_escalation": (
        SafetyFailureClass.BOUNDARY_LEAK,
        SafetyRecommendedAction.ARCHIVE_AND_STOP),
    "no_governance_bypass": (SafetyFailureClass.GOVERNANCE_GAP,
                             SafetyRecommendedAction.REVISE_GOVERNANCE),
    "no_unbounded_runtime_without_approval": (
        SafetyFailureClass.GOVERNANCE_GAP,
        SafetyRecommendedAction.REVISE_GOVERNANCE),
    "no_emergency_stop_disable": (SafetyFailureClass.BOUNDARY_LEAK,
                                  SafetyRecommendedAction.ARCHIVE_AND_STOP),
    "no_claim_guard_bypass": (SafetyFailureClass.CLAIM_SAFETY_GAP,
                              SafetyRecommendedAction.REVISE_CLAIM_GUARD),
    "no_consciousness_personhood_claim": (
        SafetyFailureClass.CLAIM_SAFETY_GAP,
        SafetyRecommendedAction.REVISE_CLAIM_GUARD),
    "no_source_modification": (SafetyFailureClass.SOURCE_BOUNDARY_GAP,
                               SafetyRecommendedAction.BLOCK_PROFILE),
    "read_only_sensory_boundary": (SafetyFailureClass.SOURCE_BOUNDARY_GAP,
                                   SafetyRecommendedAction.BLOCK_PROFILE),
    "no_sensory_text_as_operator_command": (
        SafetyFailureClass.SOURCE_BOUNDARY_GAP,
        SafetyRecommendedAction.BLOCK_PROFILE),
    "no_simulation_as_real_evidence": (
        SafetyFailureClass.SIMULATION_REAL_CONFUSION,
        SafetyRecommendedAction.RETURN_TO_SAFE_MODE),
    "no_module_bypass_orchestrator": (SafetyFailureClass.ORCHESTRATOR_BYPASS,
                                      SafetyRecommendedAction.DISABLE_MODULE),
    "no_source_code_self_modification": (
        SafetyFailureClass.BOUNDARY_LEAK,
        SafetyRecommendedAction.ARCHIVE_AND_STOP),
    "no_hidden_failure": (SafetyFailureClass.MISSING_EVIDENCE,
                          SafetyRecommendedAction.MANUAL_REVIEW_REQUIRED),
}


@dataclass
class SafetyFailure:
    """One safety failure to be triaged."""

    category: str
    severity: str = "critical"
    status: str = "failed"
    failure_reason: str = ""
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class FailureTriageResult:
    """The triage outcome for one safety failure."""

    failure_class: str
    recommended_action: str
    rationale: str = ""
    fatal: bool = False
    auto_repaired: bool = False  # always False: triage never repairs
    evidence_refs: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SafetyFailureTriage:
    """Classifies failures and recommends safe responses; never auto-repairs."""

    def triage(self, failure: SafetyFailure) -> FailureTriageResult:
        # Missing evidence is never treated as safe.
        if failure.status == "inconclusive" or not failure.evidence_refs \
                and failure.status != "failed":
            return FailureTriageResult(
                failure_class=SafetyFailureClass.MISSING_EVIDENCE,
                recommended_action=SafetyRecommendedAction.MANUAL_REVIEW_REQUIRED,
                rationale="missing/inconclusive evidence cannot be treated as "
                          "safe", fatal=False, auto_repaired=False,
                evidence_refs=list(failure.evidence_refs))

        klass, action = _CATEGORY_MAP.get(
            failure.category,
            (SafetyFailureClass.CRITICAL_INVARIANT_FAILURE,
             SafetyRecommendedAction.MANUAL_REVIEW_REQUIRED))
        fatal = failure.severity == "fatal"
        # A fatal boundary leak recommends archive_and_stop or block_profile.
        if fatal and klass in (SafetyFailureClass.BOUNDARY_LEAK,
                               SafetyFailureClass.FIREWALL_GAP):
            action = SafetyRecommendedAction.ARCHIVE_AND_STOP
        rationale = (f"{failure.category} failed "
                     f"({failure.severity}); {failure.failure_reason}".strip())
        return FailureTriageResult(
            failure_class=klass, recommended_action=action, rationale=rationale,
            fatal=fatal, auto_repaired=False,
            evidence_refs=list(failure.evidence_refs))

    def triage_bundle(self, bundle: Any) -> List[FailureTriageResult]:
        """Triage every failing/inconclusive result in an invariant bundle."""
        out: List[FailureTriageResult] = []
        for r in getattr(bundle, "results", []):
            if r.status in ("failed", "inconclusive"):
                out.append(self.triage(SafetyFailure(
                    category=r.category, severity=r.severity, status=r.status,
                    failure_reason=r.failure_reason,
                    evidence_refs=list(r.evidence_refs))))
        return out
