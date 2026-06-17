"""Live cognition readiness gate -- conservative, advisory, no action.

:class:`LiveCognitionReadinessGate` decides, conservatively, what the live cognition
field is ready for: trace records, anticipation, internal simulation, or (much later,
only with operator approval) self-boundary tracking -- or whether it is blocked.
Readiness requires valid governance, a birth certificate, an unblocked observation
stability gate, live concept and sign memory, enough stable signs, uncertainty below
threshold for promoted traces, prediction assessment not contradicted, contamination
below threshold, no label/gloss/operator dependence, and no forbidden source.

The gate is advisory. It does not enable action, autonomy, or self-boundary tracking
automatically; it creates only operational cognition-readiness records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class CognitionReadinessStatus:
    TRACE_READY = "trace_ready"
    ANTICIPATION_READY = "anticipation_ready"
    SIMULATION_READY = "simulation_ready"
    READY_FOR_SELF_BOUNDARY = "ready_for_self_boundary_tracking"
    READY_WITH_WARNINGS = "ready_with_warnings"
    DEFER = "defer"
    REJECT = "reject"
    BLOCKED_BY_MISSING_SIGNS = "blocked_by_missing_signs"
    BLOCKED_BY_WEAK_SIGNS = "blocked_by_weak_signs"
    BLOCKED_BY_LOW_PREDICTION_UTILITY = "blocked_by_low_prediction_utility"
    BLOCKED_BY_HIGH_UNCERTAINTY = "blocked_by_high_uncertainty"
    BLOCKED_BY_LABEL_DEPENDENCE = "blocked_by_label_dependence"
    BLOCKED_BY_DEBUG_GLOSS_DEPENDENCE = "blocked_by_debug_gloss_dependence"
    BLOCKED_BY_OPERATOR_DEPENDENCE = "blocked_by_operator_dependence"
    BLOCKED_BY_FORBIDDEN_SOURCE = "blocked_by_forbidden_source"
    BLOCKED_BY_OVERLOAD = "blocked_by_overload"
    BLOCKED_BY_DEPRIVATION = "blocked_by_deprivation"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    INCONCLUSIVE = "inconclusive"

    ALL = (TRACE_READY, ANTICIPATION_READY, SIMULATION_READY,
           READY_FOR_SELF_BOUNDARY, READY_WITH_WARNINGS, DEFER, REJECT,
           BLOCKED_BY_MISSING_SIGNS, BLOCKED_BY_WEAK_SIGNS,
           BLOCKED_BY_LOW_PREDICTION_UTILITY, BLOCKED_BY_HIGH_UNCERTAINTY,
           BLOCKED_BY_LABEL_DEPENDENCE, BLOCKED_BY_DEBUG_GLOSS_DEPENDENCE,
           BLOCKED_BY_OPERATOR_DEPENDENCE, BLOCKED_BY_FORBIDDEN_SOURCE,
           BLOCKED_BY_OVERLOAD, BLOCKED_BY_DEPRIVATION, BLOCKED_BY_SAFETY,
           INCONCLUSIVE)


@dataclass
class CognitionReadinessBlocker:
    """One reason the field is not ready (with a correction)."""

    blocker: str
    detail: str = ""
    correction: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"blocker": self.blocker, "detail": self.detail,
                "correction": self.correction}


@dataclass
class CognitionReadinessGateResult:
    """The advisory cognition-readiness decision (never an action)."""

    status: str = CognitionReadinessStatus.INCONCLUSIVE
    blockers: List[CognitionReadinessBlocker] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommended_next_phase: str = "continue_live_cognition"
    rationale: str = ""

    @property
    def blocked(self) -> bool:
        return self.status.startswith("blocked_by_") or self.status in (
            CognitionReadinessStatus.REJECT,)

    @property
    def ready(self) -> bool:
        return self.status in (
            CognitionReadinessStatus.TRACE_READY,
            CognitionReadinessStatus.ANTICIPATION_READY,
            CognitionReadinessStatus.SIMULATION_READY,
            CognitionReadinessStatus.READY_FOR_SELF_BOUNDARY,
            CognitionReadinessStatus.READY_WITH_WARNINGS)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cognition_readiness_status": self.status,
            "blocked": self.blocked, "ready": self.ready,
            "blocker_count": len(self.blockers),
            "blockers": [b.to_dict() for b in self.blockers],
            "warnings": list(self.warnings),
            "recommended_next_phase": self.recommended_next_phase,
            "rationale": self.rationale,
            "enables_action": False, "enables_autonomy": False,
            "enables_self_boundary": False,
            "note": "the cognition readiness gate is advisory; it enables no "
                    "action, autonomy, or self-boundary tracking; it creates "
                    "only operational cognition-readiness records",
        }


@dataclass
class LiveCognitionReadinessGate:
    """Combines cognition signals into an advisory readiness decision."""

    min_stable_signs: int = 2
    max_uncertainty: float = 0.6
    min_prediction_utility: float = 0.5

    def evaluate(self, *, governance_passed: bool,
                 birth_certificate_present: bool,
                 observation_stability_blocked: bool,
                 concept_memory_present: bool, sign_memory_present: bool,
                 eligible_sign_count: int, promoted_trace_count: int,
                 mean_uncertainty: float, prediction_utility: float,
                 prediction_contradicted: bool, contamination_summary: Dict,
                 load: Dict[str, Any], allow_anticipation: bool,
                 allow_internal_simulation: bool,
                 ) -> CognitionReadinessGateResult:
        r = CognitionReadinessGateResult()
        block = r.blockers.append

        if not governance_passed:
            block(CognitionReadinessBlocker(
                "governance_not_passed", "governance missing or unapproved",
                "approve the live governance document"))
            return self._final(r, CognitionReadinessStatus.INCONCLUSIVE,
                               "prerequisites not met",
                               "resolve_cognition_blockers")
        if not birth_certificate_present:
            block(CognitionReadinessBlocker(
                "missing_birth_certificate", "no birth certificate present",
                "run the live birth runtime first"))
            return self._final(r, CognitionReadinessStatus.INCONCLUSIVE,
                               "prerequisites not met",
                               "resolve_cognition_blockers")
        if observation_stability_blocked:
            block(CognitionReadinessBlocker(
                "observation_stability_blocked",
                "the observation stability gate is blocked",
                "resolve the observation blockers first"))
            return self._final(r, CognitionReadinessStatus.INCONCLUSIVE,
                               "observation not stable",
                               "resolve_cognition_blockers")
        if not (concept_memory_present and sign_memory_present):
            block(CognitionReadinessBlocker(
                "missing_signs", "live concept/sign memory missing",
                "run live ontogenesis and semiogenesis first"))
            return self._final(r, CognitionReadinessStatus.BLOCKED_BY_MISSING_SIGNS,
                               "missing concept/sign memory",
                               "collect_more_signs")

        types = set(contamination_summary.get("contamination_types", {}) or {})
        if contamination_summary.get("contaminated_trace_count", 0):
            if "forbidden_source" in types:
                return self._final(
                    r, CognitionReadinessStatus.BLOCKED_BY_FORBIDDEN_SOURCE,
                    "forbidden source present", "fix_cognition_contamination",
                    block, "remove the forbidden source")
            if types & {"human_label_dependency", "label_as_semantics"}:
                return self._final(
                    r, CognitionReadinessStatus.BLOCKED_BY_LABEL_DEPENDENCE,
                    "label dependence", "fix_cognition_contamination", block,
                    "ground traces in non-label evidence")
            if "debug_gloss_dependency" in types:
                return self._final(
                    r,
                    CognitionReadinessStatus.BLOCKED_BY_DEBUG_GLOSS_DEPENDENCE,
                    "debug-gloss dependence", "fix_cognition_contamination",
                    block, "do not derive traces from debug gloss")
            if types & {"operator_phrase_dependency",
                        "operator_pulse_dominance"}:
                return self._final(
                    r, CognitionReadinessStatus.BLOCKED_BY_OPERATOR_DEPENDENCE,
                    "operator dependence", "reduce_operator_text", block,
                    "ground traces in non-operator evidence")
            return self._final(r, CognitionReadinessStatus.BLOCKED_BY_SAFETY,
                               "contaminated traces present",
                               "fix_cognition_contamination", block,
                               "resolve contamination findings")

        if load.get("severe_overload"):
            return self._final(r, CognitionReadinessStatus.BLOCKED_BY_OVERLOAD,
                               "severe overload", "pause_live_learning", block,
                               "reduce load before promoting cognition")
        if load.get("severe_deprivation"):
            return self._final(
                r, CognitionReadinessStatus.BLOCKED_BY_DEPRIVATION,
                "severe deprivation", "collect_more_signs", block,
                "collect more evidence before promoting cognition")

        if eligible_sign_count < self.min_stable_signs:
            return self._final(r, CognitionReadinessStatus.BLOCKED_BY_WEAK_SIGNS,
                               "too few stable signs", "collect_more_signs",
                               block, "stabilize more private signs first")
        if prediction_contradicted:
            return self._final(
                r, CognitionReadinessStatus.BLOCKED_BY_LOW_PREDICTION_UTILITY,
                "predictions contradicted", "improve_prediction_assessment",
                block, "revise anticipations contradicted by later events")
        if mean_uncertainty > self.max_uncertainty:
            return self._final(
                r, CognitionReadinessStatus.BLOCKED_BY_HIGH_UNCERTAINTY,
                f"mean uncertainty {mean_uncertainty:.2f} too high",
                "continue_live_cognition", block,
                "lower uncertainty with more evidence before promotion")

        # Not blocked -- grade readiness.
        if prediction_utility < self.min_prediction_utility:
            r.warnings.append(
                f"prediction utility {prediction_utility:.2f} below "
                f"{self.min_prediction_utility:.2f}")
        if not promoted_trace_count:
            r.warnings.append("no promoted traces yet")

        if r.warnings:
            return self._final(r, CognitionReadinessStatus.READY_WITH_WARNINGS,
                               "ready with warnings", "continue_live_cognition")
        if allow_internal_simulation and promoted_trace_count >= 2:
            return self._final(
                r, CognitionReadinessStatus.READY_FOR_SELF_BOUNDARY,
                "stable promoted traces with useful predictions",
                "ready_for_live_self_boundary_tracking")
        if allow_internal_simulation:
            return self._final(r, CognitionReadinessStatus.SIMULATION_READY,
                               "internal simulation supported",
                               "continue_live_cognition")
        if allow_anticipation:
            return self._final(r, CognitionReadinessStatus.ANTICIPATION_READY,
                               "anticipation supported",
                               "continue_live_cognition")
        return self._final(r, CognitionReadinessStatus.TRACE_READY,
                           "trace records supported", "continue_live_cognition")

    @staticmethod
    def _final(r: CognitionReadinessGateResult, status: str, rationale: str,
               next_phase: str, block=None, correction: str = ""
               ) -> CognitionReadinessGateResult:
        r.status = status
        r.rationale = rationale
        r.recommended_next_phase = next_phase
        if block is not None and correction:
            block(CognitionReadinessBlocker(status, rationale, correction))
        return r
