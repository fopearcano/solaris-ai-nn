"""Live stability gate -- an advisory readiness decision (never an action).

:class:`LiveStabilityGate` combines governance, the birth certificate, safety,
source health, source diet, overload/deprivation, and quarantine rate into one
advisory readiness status. It answers "is the live field stable enough to continue
observation, to run metabolism calibration, or (with strong caveats) to permit a
narrow, operator-approved ontogenesis experiment later?" -- and, crucially, what to
correct first when it is not.

The gate is advisory only. It does not start any phase, change any feeder, enable
learning, or claim that Solaris is conscious, alive, or an agent. A blocked gate is
a normal, healthy outcome of the first hours of observation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LiveStabilityStatus:
    READY_FOR_OBSERVATION_CONTINUATION = "ready_for_observation_continuation"
    READY_FOR_METABOLISM_CALIBRATION = "ready_for_metabolism_calibration"
    READY_FOR_LIMITED_ONTOGENESIS = "ready_for_limited_ontogenesis"
    READY_WITH_WARNINGS = "ready_with_warnings"
    BLOCKED_BY_GOVERNANCE = "blocked_by_governance"
    BLOCKED_BY_QUARANTINE_RATE = "blocked_by_quarantine_rate"
    BLOCKED_BY_FORBIDDEN_SOURCE = "blocked_by_forbidden_source"
    BLOCKED_BY_OVERLOAD = "blocked_by_overload"
    BLOCKED_BY_DEPRIVATION = "blocked_by_deprivation"
    BLOCKED_BY_OPERATOR_TEXT_DOMINANCE = "blocked_by_operator_text_dominance"
    BLOCKED_BY_MISSING_BIRTH_CERTIFICATE = "blocked_by_missing_birth_certificate"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    INCONCLUSIVE = "inconclusive"

    ALL = (READY_FOR_OBSERVATION_CONTINUATION, READY_FOR_METABOLISM_CALIBRATION,
           READY_FOR_LIMITED_ONTOGENESIS, READY_WITH_WARNINGS,
           BLOCKED_BY_GOVERNANCE, BLOCKED_BY_QUARANTINE_RATE,
           BLOCKED_BY_FORBIDDEN_SOURCE, BLOCKED_BY_OVERLOAD,
           BLOCKED_BY_DEPRIVATION, BLOCKED_BY_OPERATOR_TEXT_DOMINANCE,
           BLOCKED_BY_MISSING_BIRTH_CERTIFICATE, BLOCKED_BY_SAFETY,
           INCONCLUSIVE)


@dataclass
class LiveStabilityBlocker:
    """One reason the field is not ready for a later phase (with a fix)."""

    blocker: str
    detail: str = ""
    correction: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"blocker": self.blocker, "detail": self.detail,
                "correction": self.correction}


@dataclass
class LiveStabilityGateResult:
    """The advisory stability decision (never an action)."""

    status: str = LiveStabilityStatus.INCONCLUSIVE
    blockers: List[LiveStabilityBlocker] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommended_next_phase: str = "continue_observation"
    corrections: List[str] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return self.status.startswith("blocked_by_")

    @property
    def ready_for_metabolism(self) -> bool:
        return self.status in (
            LiveStabilityStatus.READY_FOR_METABOLISM_CALIBRATION,
            LiveStabilityStatus.READY_FOR_LIMITED_ONTOGENESIS)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "live_stability_status": self.status,
            "blocked": self.blocked,
            "blocker_count": len(self.blockers),
            "blockers": [b.to_dict() for b in self.blockers],
            "warnings": list(self.warnings),
            "recommended_next_phase": self.recommended_next_phase,
            "corrections": list(self.corrections),
            "ready_for_metabolism_calibration": self.ready_for_metabolism,
            "starts_any_phase": False, "changes_feeders": False,
            "enables_learning": False,
            "note": "the stability gate is advisory only; it starts no phase, "
                    "changes no feeder, and enables no learning; a blocked gate "
                    "is a normal, healthy outcome of early observation",
        }


@dataclass
class LiveStabilityGate:
    """Combines observation signals into an advisory readiness decision."""

    max_quarantine_rate: float = 0.25

    def evaluate(self, *, governance_passed: bool,
                 birth_certificate_present: bool, safety_ok: bool,
                 source_health_summary: Dict[str, Any],
                 source_diet: Dict[str, Any], load: Dict[str, Any],
                 quarantine_rate: float) -> LiveStabilityGateResult:
        r = LiveStabilityGateResult()
        block = r.blockers.append

        # Hard blockers (each names what to correct first).
        if not governance_passed:
            block(LiveStabilityBlocker(
                "governance_not_passed",
                "governance is missing or not approved",
                "review and approve the live governance document"))
            r.status = LiveStabilityStatus.BLOCKED_BY_GOVERNANCE
        elif not safety_ok:
            block(LiveStabilityBlocker(
                "safety_violation", "a safety check failed",
                "resolve the reported safety findings before continuing"))
            r.status = LiveStabilityStatus.BLOCKED_BY_SAFETY
        elif not birth_certificate_present:
            block(LiveStabilityBlocker(
                "missing_birth_certificate",
                "no birth certificate was found in state",
                "run the live birth runtime to issue a birth certificate"))
            r.status = LiveStabilityStatus.BLOCKED_BY_MISSING_BIRTH_CERTIFICATE
        elif source_health_summary.get("live_forbidden_source_count", 0):
            block(LiveStabilityBlocker(
                "forbidden_source_present",
                "a forbidden source produced events",
                "remove the forbidden source from feeders and inbox"))
            r.status = LiveStabilityStatus.BLOCKED_BY_FORBIDDEN_SOURCE
        elif quarantine_rate > self.max_quarantine_rate:
            block(LiveStabilityBlocker(
                "quarantine_rate_too_high",
                f"quarantine rate {quarantine_rate:.0%} exceeds bound",
                "inspect quarantined events and fix the noisiest feeder"))
            r.status = LiveStabilityStatus.BLOCKED_BY_QUARANTINE_RATE
        elif load.get("severe_overload"):
            block(LiveStabilityBlocker(
                "severe_overload", "the field is severely overloaded",
                "ask the operator to slow or pause the noisiest feeder"))
            r.status = LiveStabilityStatus.BLOCKED_BY_OVERLOAD
        elif load.get("severe_deprivation"):
            block(LiveStabilityBlocker(
                "severe_deprivation", "the field is severely deprived",
                "ask the operator to enable more read-only feeders"))
            r.status = LiveStabilityStatus.BLOCKED_BY_DEPRIVATION
        elif source_diet.get("balance") in ("operator_pulse_dominant",
                                            "human_text_dominant"):
            block(LiveStabilityBlocker(
                "operator_text_dominant",
                "operator pulse / human text dominates the field",
                "broaden the source diet; operator pulse is stimulus, not the "
                "primary source"))
            r.status = LiveStabilityStatus.BLOCKED_BY_OPERATOR_TEXT_DOMINANCE

        if r.blocked:
            r.recommended_next_phase = "fix_blockers_then_continue_observation"
            r.corrections = [b.correction for b in r.blockers if b.correction]
            return r

        # Not blocked -- grade readiness and collect warnings.
        if load.get("load_status") in ("mild_overload", "mild_deprivation",
                                       "mixed"):
            r.warnings.append(f"load status is {load.get('load_status')!r}")
        if source_diet.get("balance") in ("single_source", "mild_dominance"):
            r.warnings.append(f"source diet is {source_diet.get('balance')!r}")
        if source_health_summary.get("live_noisy_source_count", 0):
            r.warnings.append("one or more sources are noisy but usable")
        if load.get("requires_operator_review"):
            r.warnings.append("mixed load picture requires operator review")

        live_sources = int(source_health_summary.get("live_source_count", 0))
        healthy = int(source_health_summary.get("live_healthy_source_count", 0))
        balanced = source_diet.get("balance") == "balanced"

        if r.warnings:
            r.status = LiveStabilityStatus.READY_WITH_WARNINGS
            r.recommended_next_phase = "continue_observation"
        elif healthy >= 3 and balanced and not load.get(
                "blocks_ontogenesis_recommendation"):
            # Stable, balanced, healthy: metabolism calibration is appropriate;
            # limited ontogenesis remains an operator-approved future step.
            r.status = LiveStabilityStatus.READY_FOR_METABOLISM_CALIBRATION
            r.recommended_next_phase = "run_metabolism_calibration"
        elif healthy >= 1:
            r.status = LiveStabilityStatus.READY_FOR_OBSERVATION_CONTINUATION
            r.recommended_next_phase = "continue_observation"
        else:
            r.status = LiveStabilityStatus.INCONCLUSIVE
            r.recommended_next_phase = "continue_observation"
            r.warnings.append("insufficient healthy sources to decide")
        return r
