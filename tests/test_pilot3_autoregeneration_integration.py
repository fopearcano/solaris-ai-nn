"""Pilot-3 <-> Auto-regeneration: action loop detected; dry-run proposed.

Pilot-3 surfaces auto-regeneration-style adaptive repair proposals through the
embodied reviews: a high veto / action-loop run proposes switching to dry-run or
reducing the action rate, and the weekly review raises an action-loop warning.
"""

from __future__ import annotations

from solaris_ai_nn.pilot3 import (
    Pilot3DailyRecommendation,
    Pilot3DailyReviewBuilder,
    Pilot3WeeklyReviewBuilder,
)


def test_action_loop_detected_weekly(tmp_path):
    b = Pilot3WeeklyReviewBuilder(base_dir=str(tmp_path))
    review = b.build(1, [{"veto_count": 8}, {"veto_count": 9}])
    assert review.action_loop_warning is True
    assert "reduce_action_complexity_or_switch_to_dry_run" \
        in review.next_window_recommendation


def test_switch_to_dry_run_proposed(tmp_path):
    b = Pilot3DailyReviewBuilder(base_dir=str(tmp_path))
    # A high veto rate is a repeated-veto/action loop -> switch to dry-run.
    review = b.build(1, {"action_count": 10, "veto_count": 9})
    assert review.recommendation == \
        Pilot3DailyRecommendation.SWITCH_TO_DRY_RUN


def test_reduce_action_rate_proposed(tmp_path):
    b = Pilot3DailyReviewBuilder(base_dir=str(tmp_path))
    review = b.build(1, {"action_count": 5, "autoregeneration_warnings": 3})
    assert review.recommendation == \
        Pilot3DailyRecommendation.REDUCE_ACTION_RATE


def test_repair_proposals_are_safe():
    # The allowed Pilot-3 repair proposals never include real-world actuation.
    safe = {Pilot3DailyRecommendation.REDUCE_ACTION_RATE,
            Pilot3DailyRecommendation.SWITCH_TO_DRY_RUN,
            Pilot3DailyRecommendation.RETURN_TO_READ_ONLY,
            Pilot3DailyRecommendation.PAUSE_AND_REVIEW,
            Pilot3DailyRecommendation.ARCHIVE_AND_STOP}
    assert safe <= set(Pilot3DailyRecommendation.ALL)
