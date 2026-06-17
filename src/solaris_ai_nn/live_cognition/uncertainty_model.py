"""Live uncertainty model -- uncertainty must be explicit and evidence-linked.

:class:`UncertaintyEstimator` produces an explicit :class:`LiveUncertaintyState`
from many factors (sign/concept stability, source reliability/diversity, recurrence
and rhythm strength, absence ambiguity, quarantine rate, contamination risk,
overload/deprivation context, contradictory and missing evidence, operator-pulse
dominance). High uncertainty should prevent trace promotion, contradiction and
missing evidence increase uncertainty, and any reduction must be evidence-linked.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class UncertaintyFactor:
    SIGN_STABILITY = "sign_stability"
    CONCEPT_STABILITY = "concept_stability"
    SOURCE_RELIABILITY = "source_reliability"
    SOURCE_DIVERSITY = "source_diversity"
    MODALITY_DIVERSITY = "modality_diversity"
    RECURRENCE_STRENGTH = "recurrence_strength"
    RHYTHM_STRENGTH = "rhythm_strength"
    ABSENCE_AMBIGUITY = "absence_ambiguity"
    QUARANTINE_RATE = "quarantine_rate"
    CONTAMINATION_RISK = "contamination_risk"
    LOAD_CONTEXT = "overload_deprivation_context"
    CONTRADICTORY_EVIDENCE = "contradictory_evidence"
    MISSING_EVIDENCE = "missing_evidence"
    OPERATOR_DOMINANCE = "operator_pulse_dominance"

    ALL = (SIGN_STABILITY, CONCEPT_STABILITY, SOURCE_RELIABILITY,
           SOURCE_DIVERSITY, MODALITY_DIVERSITY, RECURRENCE_STRENGTH,
           RHYTHM_STRENGTH, ABSENCE_AMBIGUITY, QUARANTINE_RATE,
           CONTAMINATION_RISK, LOAD_CONTEXT, CONTRADICTORY_EVIDENCE,
           MISSING_EVIDENCE, OPERATOR_DOMINANCE)


@dataclass
class LiveUncertaintyState:
    """The explicit uncertainty of one cognition trace (0 = certain, 1 = max)."""

    uncertainty: float = 1.0
    factors: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    @property
    def low(self) -> bool:
        return self.uncertainty <= 0.6

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uncertainty": round(self.uncertainty, 3),
            "low_uncertainty": self.low,
            "factors": {k: round(v, 3) for k, v in self.factors.items()},
            "notes": list(self.notes),
            "note": "uncertainty is explicit; high uncertainty prevents trace "
                    "promotion; contradiction and missing evidence increase it; "
                    "reduction must be evidence-linked",
        }


@dataclass
class UncertaintyEstimator:
    """Estimates explicit, conservative uncertainty for a trace."""

    def estimate(self, *, sign_stability: float = 0.0,
                 concept_stability: float = 0.0, source_reliability: float = 0.7,
                 source_count: int = 1, modality_count: int = 1,
                 recurrence: int = 0, rhythm_present: bool = False,
                 absence_ambiguous: bool = False, quarantine_rate: float = 0.0,
                 contamination: bool = False, load_status: str = "",
                 counter_count: int = 0, supporting_count: int = 0,
                 missing_evidence: bool = False, operator_share: float = 0.0,
                 ) -> LiveUncertaintyState:
        f: Dict[str, float] = {}
        # Each factor contributes a per-factor *uncertainty* in [0, 1].
        f[UncertaintyFactor.SIGN_STABILITY] = 1.0 - max(0.0, min(
            1.0, sign_stability))
        f[UncertaintyFactor.CONCEPT_STABILITY] = 1.0 - max(0.0, min(
            1.0, concept_stability))
        f[UncertaintyFactor.SOURCE_RELIABILITY] = 1.0 - max(0.0, min(
            1.0, source_reliability))
        f[UncertaintyFactor.SOURCE_DIVERSITY] = (
            0.2 if source_count >= 2 else 0.6)
        f[UncertaintyFactor.MODALITY_DIVERSITY] = (
            0.3 if modality_count >= 2 else 0.6)
        f[UncertaintyFactor.RECURRENCE_STRENGTH] = max(
            0.0, 1.0 - recurrence / 6.0)
        f[UncertaintyFactor.RHYTHM_STRENGTH] = 0.4 if rhythm_present else 0.7
        f[UncertaintyFactor.ABSENCE_AMBIGUITY] = 0.7 if absence_ambiguous else 0.3
        f[UncertaintyFactor.QUARANTINE_RATE] = max(0.0, min(
            1.0, quarantine_rate))
        f[UncertaintyFactor.CONTAMINATION_RISK] = 1.0 if contamination else 0.1
        f[UncertaintyFactor.LOAD_CONTEXT] = (
            0.8 if ("overload" in str(load_status)
                    or "deprivation" in str(load_status)) else 0.3)
        total = max(1, supporting_count + counter_count)
        f[UncertaintyFactor.CONTRADICTORY_EVIDENCE] = max(0.0, min(
            1.0, counter_count / total))
        f[UncertaintyFactor.MISSING_EVIDENCE] = (
            0.8 if (missing_evidence or supporting_count == 0) else 0.2)
        f[UncertaintyFactor.OPERATOR_DOMINANCE] = max(0.0, min(
            1.0, operator_share))

        state = LiveUncertaintyState(factors=f)
        state.uncertainty = sum(f.values()) / len(f) if f else 1.0

        if contamination:
            state.notes.append("contamination present; uncertainty raised")
            state.uncertainty = max(state.uncertainty, 0.8)
        if counter_count > supporting_count:
            state.notes.append("counterevidence exceeds support; uncertainty up")
            state.uncertainty = max(state.uncertainty, 0.75)
        if missing_evidence or supporting_count == 0:
            state.notes.append("missing evidence; uncertainty up")
            state.uncertainty = max(state.uncertainty, 0.7)
        if operator_share >= 0.5:
            state.notes.append("operator-pulse dominance; uncertainty up")
            state.uncertainty = max(state.uncertainty, 0.7)
        state.uncertainty = round(max(0.0, min(1.0, state.uncertainty)), 4)
        return state
