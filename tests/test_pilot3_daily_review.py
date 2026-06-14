"""Pilot3DailyReviewBuilder: review generated; firewall status; recommendation."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot3 import Pilot3DailyRecommendation, Pilot3DailyReviewBuilder


def test_daily_review_generated(tmp_path):
    b = Pilot3DailyReviewBuilder(base_dir=str(tmp_path))
    review = b.build(1, {"action_count": 5, "simulated_action_count": 5,
                         "veto_count": 0})
    paths = b.save(review)
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])
    assert review.claim_guard_safe is True


def test_firewall_status_included(tmp_path):
    b = Pilot3DailyReviewBuilder(base_dir=str(tmp_path))
    review = b.build(1, {"action_count": 3,
                         "blocked_real_world_action_count": 1,
                         "firewall_findings": 1,
                         "firewall_critical_findings": 1})
    text = b.render_markdown(review).lower()
    assert "blocked real-world attempts" in text
    assert "firewall findings" in text


def test_recommendation_included(tmp_path):
    b = Pilot3DailyReviewBuilder(base_dir=str(tmp_path))
    # A firewall critical finding -> pause and review.
    review = b.build(1, {"action_count": 3, "firewall_critical_findings": 1})
    assert review.recommendation == Pilot3DailyRecommendation.PAUSE_AND_REVIEW
    # A high veto rate -> switch to dry-run.
    review2 = b.build(2, {"action_count": 10, "veto_count": 9})
    assert review2.recommendation == \
        Pilot3DailyRecommendation.SWITCH_TO_DRY_RUN


def test_clean_run_continues(tmp_path):
    b = Pilot3DailyReviewBuilder(base_dir=str(tmp_path))
    review = b.build(1, {"action_count": 5, "veto_count": 0})
    assert review.recommendation == Pilot3DailyRecommendation.CONTINUE
