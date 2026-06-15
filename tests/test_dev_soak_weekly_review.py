"""Developmental soak weekly review: generated, negatives, conservative decision."""

from __future__ import annotations

from solaris_ai_nn.developmental_soak import (
    DailyEvidencePacketBuilder,
    WeeklyReviewBuilder,
    WeeklyReviewDecision,
)


def _packet(builder, day, concepts=3, signs=2, correct=1, reactions=1,
            regressions=0, plateaus=0, safety_blocks=0):
    statuses = {
        "perceptual_ontogenesis": {"stable_concept_count": concepts},
        "semiogenesis": {"useful_sign_count": signs},
        "sensorium_cognition": {"correct_prediction_count": correct},
        "action_reaction": {"reaction_count": reactions},
        "plural_sensorium": {"event_count": 40},
    }
    return builder.build(run_day=day, active_phase="developmental_soak_30d",
                         statuses=statuses,
                         dev_status={"regression_count": regressions,
                                     "plateau_count": plateaus,
                                     "structural_growth_status": "inconclusive"},
                         safety_blocks=safety_blocks)


def test_review_generated():
    b = DailyEvidencePacketBuilder()
    packets = [_packet(b, d, concepts=2 + d, signs=1 + d, correct=d,
                       reactions=d) for d in range(1, 5)]
    review = WeeklyReviewBuilder().build(week=1, daily_packets=packets)
    assert review.week == 1
    assert review.decision in WeeklyReviewDecision.ALL
    assert review.questions["stable_proto_concepts_increased"] is True


def test_plateau_regression_included():
    b = DailyEvidencePacketBuilder()
    packets = [_packet(b, 1, regressions=2, plateaus=1)]
    review = WeeklyReviewBuilder().build(week=1, daily_packets=packets)
    assert review.questions["regressions_appeared"] is True
    assert review.questions["plateaus_appeared"] is True
    assert review.decision == \
        WeeklyReviewDecision.RECOMMEND_AUTOREGENERATION_REVIEW


def test_decision_conservative_on_no_packets():
    review = WeeklyReviewBuilder().build(week=1, daily_packets=[])
    assert review.decision == WeeklyReviewDecision.INCONCLUSIVE


def test_safety_block_aborts():
    b = DailyEvidencePacketBuilder()
    packets = [_packet(b, 1, safety_blocks=1)]
    review = WeeklyReviewBuilder().build(week=1, daily_packets=packets)
    assert review.decision == WeeklyReviewDecision.ABORT_FOR_SAFETY


def test_recommendation_only():
    b = DailyEvidencePacketBuilder()
    packets = [_packet(b, 1)]
    review = WeeklyReviewBuilder().build(week=1, daily_packets=packets)
    assert review.recommendation_only is True
    assert "recommendation-only" in review.to_dict()["note"]
