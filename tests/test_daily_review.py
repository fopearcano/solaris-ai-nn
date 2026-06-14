"""Pilot-1 daily review: generation, recommendation, ClaimGuard scan."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot1 import DailyRecommendation, DailyReviewBuilder


def _obs(**kw):
    base = {"uptime_ratio": 1.0, "structural_change_score": 0.1,
            "proto_symbol_count": 5}
    base.update(kw)
    return base


def test_daily_review_generated(tmp_path):
    builder = DailyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _obs())
    paths = builder.save(review)
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])


def test_recommendation_present(tmp_path):
    builder = DailyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _obs())
    assert review.recommendation in DailyRecommendation.ALL


def test_safety_incidents_force_shutdown(tmp_path):
    builder = DailyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _obs(safety_incident_count=5))
    assert review.recommendation == DailyRecommendation.SAFE_SHUTDOWN


def test_claim_guard_scans_markdown(tmp_path):
    builder = DailyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _obs())
    builder.save(review)
    assert review.claim_guard_safe is True


def test_markdown_disclaims_inner_experience(tmp_path):
    builder = DailyReviewBuilder(base_dir=str(tmp_path))
    text = builder.render_markdown(builder.build(1, _obs()))
    assert "not inner experience" in text
