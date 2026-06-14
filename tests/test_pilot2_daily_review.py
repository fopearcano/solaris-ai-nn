"""Pilot-2 daily review: generated, source status, recommendation."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot2 import Pilot2DailyRecommendation, Pilot2DailyReviewBuilder


def _rollup(**kw):
    base = {"event_count": 10, "provenance_completeness": 1.0,
            "source_status": {"j": "reliable"},
            "new_sensory_proto_symbols": 2}
    base.update(kw)
    return base


def test_daily_review_generated(tmp_path):
    builder = Pilot2DailyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollup())
    paths = builder.save(review)
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])


def test_source_status_included(tmp_path):
    builder = Pilot2DailyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollup())
    md = builder.render_markdown(review)
    assert "j: reliable" in md


def test_recommendation_present(tmp_path):
    builder = Pilot2DailyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollup())
    assert review.recommendation in Pilot2DailyRecommendation.ALL


def test_unsafe_source_disables(tmp_path):
    builder = Pilot2DailyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollup(unsafe_source_count=1))
    assert review.recommendation == Pilot2DailyRecommendation.DISABLE_SOURCE


def test_claim_guard_scans_markdown(tmp_path):
    builder = Pilot2DailyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollup())
    builder.save(review)
    assert review.claim_guard_safe is True
