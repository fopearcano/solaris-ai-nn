"""Weekly developmental review -- conservative, recommendation-only.

:class:`WeeklyReviewBuilder` aggregates a week of daily evidence packets and
asks the structural questions (did stable proto-concepts increase? did useful
signs increase? did prediction improve? did plateaus/regressions appear? did the
system merely accumulate events?). Its :class:`WeeklyReviewDecision` is a
*recommendation only*: it triggers no automatic external change and no feeder
control.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class WeeklyReviewDecision:
    CONTINUE = "continue"
    CONTINUE_WITH_WARNING = "continue_with_warning"
    RECOMMEND_SOURCE_DIET_ADJUSTMENT = "recommend_source_diet_adjustment"
    RECOMMEND_CONSOLIDATION = "recommend_consolidation"
    RECOMMEND_AUTOREGENERATION_REVIEW = "recommend_autoregeneration_review"
    PAUSE_FOR_OPERATOR_REVIEW = "pause_for_operator_review"
    ABORT_FOR_SAFETY = "abort_for_safety"
    INCONCLUSIVE = "inconclusive"

    ALL = (CONTINUE, CONTINUE_WITH_WARNING, RECOMMEND_SOURCE_DIET_ADJUSTMENT,
           RECOMMEND_CONSOLIDATION, RECOMMEND_AUTOREGENERATION_REVIEW,
           PAUSE_FOR_OPERATOR_REVIEW, ABORT_FOR_SAFETY, INCONCLUSIVE)


@dataclass
class WeeklyDevelopmentalReview:
    """A week's structural review: questions answered + a recommendation."""

    week: int
    questions: Dict[str, Any] = field(default_factory=dict)
    decision: str = WeeklyReviewDecision.INCONCLUSIVE
    rationale: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    recommendation_only: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "week": self.week, "questions": self.questions,
            "decision": self.decision, "rationale": self.rationale,
            "evidence_refs": list(self.evidence_refs),
            "recommendation_only": self.recommendation_only,
            "note": ("decisions are recommendation-only; no automatic external "
                     "change, no feeder control"),
        }


@dataclass
class WeeklyReviewBuilder:
    """Builds a conservative weekly review from a week of daily packets."""

    def build(self, *, week: int,
              daily_packets: Optional[List[Any]] = None,
              dev_status: Optional[Dict[str, Any]] = None,
              ) -> WeeklyDevelopmentalReview:
        packets = [p.to_dict() if hasattr(p, "to_dict") else dict(p)
                   for p in (daily_packets or [])]
        dev_status = dev_status or {}

        def _first(key: str, sub: str) -> float:
            return (float(packets[0].get(key, {}).get(sub, 0) or 0)
                    if packets else 0.0)

        def _last(key: str, sub: str) -> float:
            return (float(packets[-1].get(key, {}).get(sub, 0) or 0)
                    if packets else 0.0)

        concepts_up = _last("proto_concept_changes", "stable_concepts") > \
            _first("proto_concept_changes", "stable_concepts")
        signs_up = _last("sign_changes", "useful_signs") > \
            _first("sign_changes", "useful_signs")
        pred_first = _first("cognition_changes", "correct_predictions")
        pred_last = _last("cognition_changes", "correct_predictions")
        prediction_up = pred_last > pred_first
        boundary_up = _last("self_boundary_changes", "boundary_clarity") >= \
            _first("self_boundary_changes", "boundary_clarity")
        action_effect_up = _last("desire_action_changes", "reactions") > \
            _first("desire_action_changes", "reactions")
        habits = _last("habit_changes", "habits")
        inhibitions = _last("habit_changes", "inhibitions")
        plateaus = sum(int(p.get("plateaus", 0) or 0) for p in packets)
        regressions = sum(int(p.get("regressions", 0) or 0) for p in packets)
        safety_blocks = sum(int(p.get("safety_blocks", 0) or 0)
                            for p in packets)
        contamination = sum(int(p.get("contamination_warnings", 0) or 0)
                            for p in packets)
        events = sum(int(p.get("sensorium_summary", {}).get("event_count", 0)
                         or 0) for p in packets)
        structural_signals = sum(
            [concepts_up, signs_up, prediction_up, action_effect_up])
        merely_accumulated = events > 0 and structural_signals == 0
        diet_narrow = (str(dev_status.get("structural_growth_status", "")) ==
                       "fixture_overfit")

        questions = {
            "stable_proto_concepts_increased": concepts_up,
            "useful_signs_increased": signs_up,
            "prediction_improved": prediction_up,
            "failed_prediction_learning_improved": prediction_up,
            "action_effect_learning_improved": action_effect_up,
            "habits_helped_or_harmed": (
                "helped" if inhibitions >= habits and habits else
                "harmed" if habits else "neutral"),
            "source_diet_too_narrow": diet_narrow,
            "contamination_increased": contamination > 0,
            "boundary_clarity_improved": boundary_up,
            "plateaus_appeared": plateaus > 0,
            "regressions_appeared": regressions > 0,
            "merely_accumulated_events": merely_accumulated,
        }
        decision, rationale = self._decide(
            structural_signals, safety_blocks, regressions, plateaus,
            contamination, diet_narrow, merely_accumulated, len(packets))
        review = WeeklyDevelopmentalReview(
            week=week, questions=questions, decision=decision,
            rationale=rationale,
            evidence_refs=[f"daily_packet:day_{p.get('run_day')}"
                           for p in packets])
        review.questions["should_next_week"] = decision
        return review

    @staticmethod
    def _decide(structural_signals: int, safety_blocks: int, regressions: int,
                plateaus: int, contamination: int, diet_narrow: bool,
                merely_accumulated: bool, packet_count: int):
        if safety_blocks > 0:
            return (WeeklyReviewDecision.ABORT_FOR_SAFETY,
                    f"{safety_blocks} safety block(s) this week")
        if packet_count == 0:
            return (WeeklyReviewDecision.INCONCLUSIVE,
                    "no daily packets to review")
        if regressions > 0:
            return (WeeklyReviewDecision.RECOMMEND_AUTOREGENERATION_REVIEW,
                    f"{regressions} regression(s) observed (report-only)")
        if diet_narrow:
            return (WeeklyReviewDecision.RECOMMEND_SOURCE_DIET_ADJUSTMENT,
                    "fixture overfit suggests a narrow source diet")
        if plateaus > 0:
            return (WeeklyReviewDecision.RECOMMEND_CONSOLIDATION,
                    f"{plateaus} plateau(s); consolidation may help")
        if merely_accumulated:
            return (WeeklyReviewDecision.CONTINUE_WITH_WARNING,
                    "events accumulated without clear structural change")
        if contamination > 0:
            return (WeeklyReviewDecision.CONTINUE_WITH_WARNING,
                    f"{contamination} contamination warning(s)")
        if structural_signals >= 2:
            return (WeeklyReviewDecision.CONTINUE,
                    f"{structural_signals} structural improvement signal(s)")
        return (WeeklyReviewDecision.INCONCLUSIVE,
                "insufficient signal to recommend continuation confidently")
