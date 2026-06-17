"""Live prediction assessment -- assess anticipations against later events.

:class:`LivePredictionAssessment` compares each anticipation against later
live-read-only events (where available) and records the outcome: matched, partially
matched, contradicted, not-yet-observed, unobservable, ambiguous, contaminated, or
unknown. Prediction success is operational evidence only -- it does not imply
consciousness or understanding; failures and ambiguity are preserved and never
cherry-picked.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class PredictionOutcome:
    MATCHED = "matched"
    PARTIALLY_MATCHED = "partially_matched"
    CONTRADICTED = "contradicted"
    NOT_YET_OBSERVED = "not_yet_observed"
    UNOBSERVABLE = "unobservable"
    AMBIGUOUS = "ambiguous"
    CONTAMINATED = "contaminated"
    UNKNOWN = "unknown"

    ALL = (MATCHED, PARTIALLY_MATCHED, CONTRADICTED, NOT_YET_OBSERVED,
           UNOBSERVABLE, AMBIGUOUS, CONTAMINATED, UNKNOWN)


@dataclass
class PredictionScore:
    """The aggregate prediction-assessment score (no cherry-picking)."""

    assessed_count: int = 0
    matched: int = 0
    partially_matched: int = 0
    contradicted: int = 0
    not_yet_observed: int = 0
    ambiguous: int = 0
    contaminated: int = 0
    operator_text_bias_count: int = 0

    @property
    def utility(self) -> float:
        """Conservative utility: matched minus contradicted, over observed."""
        observed = self.matched + self.partially_matched + self.contradicted
        if observed == 0:
            return 0.0
        return max(0.0, (self.matched + 0.5 * self.partially_matched
                         - self.contradicted) / observed)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "live_prediction_assessment_count": self.assessed_count,
            "live_prediction_matched_count": self.matched,
            "partially_matched_count": self.partially_matched,
            "live_prediction_contradicted_count": self.contradicted,
            "not_yet_observed_count": self.not_yet_observed,
            "ambiguous_count": self.ambiguous,
            "contaminated_count": self.contaminated,
            "operator_text_bias_count": self.operator_text_bias_count,
            "prediction_utility": round(self.utility, 3),
            "note": "prediction success is operational evidence only and does "
                    "not imply consciousness/understanding; failures and "
                    "ambiguity are preserved; no cherry-picking",
        }


@dataclass
class AnticipationOutcome:
    """The assessed outcome of one anticipation."""

    anticipation_id: str
    anticipation_type: str
    outcome: str
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"anticipation_id": self.anticipation_id,
                "anticipation_type": self.anticipation_type,
                "outcome": self.outcome, "detail": self.detail}


@dataclass
class LivePredictionAssessment:
    """Assesses anticipations/simulations against later observed events."""

    def assess(self, *, anticipations: List[Any],
               later_events: Optional[List[Dict[str, Any]]] = None,
               ) -> Dict[str, Any]:
        later_events = later_events or []
        observed_sources = {ev.get("source_id", "") for ev in later_events}
        absence_sources = {ev.get("source_id", "") for ev in later_events
                           if (ev.get("quality", {}) or {}).get("is_absence")}
        score = PredictionScore()
        outcomes: List[AnticipationOutcome] = []

        for ant in anticipations:
            d = ant.to_dict() if hasattr(ant, "to_dict") else dict(ant)
            score.assessed_count += 1
            outcome = self._assess_one(d, observed_sources, absence_sources,
                                       bool(later_events))
            if d.get("contamination_findings"):
                outcome = PredictionOutcome.CONTAMINATED
            self._tally(score, outcome)
            if "operator_pulse" in (d.get("linked_concept_ids") or []) or \
                    "operator" in str(d.get("detail", "")):
                score.operator_text_bias_count += 1
            outcomes.append(AnticipationOutcome(
                anticipation_id=d.get("anticipation_id", ""),
                anticipation_type=d.get("anticipation_type", ""),
                outcome=outcome,
                detail=d.get("detail", "")))
        result = score.to_dict()
        result["outcomes"] = [o.to_dict() for o in outcomes]
        return result

    @staticmethod
    def _assess_one(d: Dict[str, Any], observed_sources: set,
                    absence_sources: set, have_events: bool) -> str:
        if not have_events:
            return PredictionOutcome.NOT_YET_OBSERVED
        atype = d.get("anticipation_type", "")
        concepts = d.get("linked_concept_ids", []) or []
        # Map anticipation to an observable signal in later events.
        if atype in ("recurrence_expected", "rhythm_continuation",
                     "next_source_likely_active", "co_occurrence_expected"):
            # Matched if any linked concept's source recurs later.
            if observed_sources:
                # Heuristic: concept ids often embed the source name.
                hit = any(any(src and src in cid for cid in concepts)
                          for src in observed_sources)
                return (PredictionOutcome.MATCHED if hit
                        else PredictionOutcome.PARTIALLY_MATCHED
                        if observed_sources else
                        PredictionOutcome.NOT_YET_OBSERVED)
            return PredictionOutcome.NOT_YET_OBSERVED
        if atype == "source_silence_likely_continues":
            if absence_sources:
                return PredictionOutcome.MATCHED
            if observed_sources:
                return PredictionOutcome.CONTRADICTED
            return PredictionOutcome.NOT_YET_OBSERVED
        if atype in ("overload_risk_expected", "deprivation_risk_expected",
                     "source_health_change_expected"):
            return PredictionOutcome.AMBIGUOUS
        return PredictionOutcome.AMBIGUOUS

    @staticmethod
    def _tally(score: PredictionScore, outcome: str) -> None:
        if outcome == PredictionOutcome.MATCHED:
            score.matched += 1
        elif outcome == PredictionOutcome.PARTIALLY_MATCHED:
            score.partially_matched += 1
        elif outcome == PredictionOutcome.CONTRADICTED:
            score.contradicted += 1
        elif outcome == PredictionOutcome.NOT_YET_OBSERVED:
            score.not_yet_observed += 1
        elif outcome == PredictionOutcome.AMBIGUOUS:
            score.ambiguous += 1
        elif outcome == PredictionOutcome.CONTAMINATED:
            score.contaminated += 1
