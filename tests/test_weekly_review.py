"""Pilot-1 weekly review: trends, stagnation warning, limitations."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot1 import WeeklyReviewBuilder


def _rollups(scores):
    return [{"structural_change_score": s, "proto_symbol_count": 5,
             "uptime_ratio": 1.0, "memory_size_bytes": 1000 + i}
            for i, s in enumerate(scores)]


def test_weekly_trend_generated(tmp_path):
    builder = WeeklyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollups([0.1, 0.2, 0.4]))
    paths = builder.save(review)
    assert os.path.exists(paths["markdown"]) and os.path.exists(paths["json"])
    assert review.structural_growth_trend == "rising"


def test_stagnation_warning_included(tmp_path):
    builder = WeeklyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollups([0.0, 0.0, 0.0]))
    # Flat structural + flat proto -> stagnation warning.
    review.proto_language_trend = "flat"
    rebuilt = builder.build(1, [{"structural_change_score": 0.0,
                                 "proto_symbol_count": 1,
                                 "uptime_ratio": 1.0} for _ in range(3)])
    assert rebuilt.stagnation_warning is True
    md = builder.render_markdown(rebuilt)
    assert "stagnation warning" in md


def test_limitations_included(tmp_path):
    builder = WeeklyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollups([0.1, 0.1]))
    assert review.limitations
    assert "## Limitations" in builder.render_markdown(review)


def test_regression_recommends_pause(tmp_path):
    builder = WeeklyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollups([0.5, 0.3, 0.1]))
    assert review.regression_warning is True
    assert review.recommendation == "pause_and_review"
