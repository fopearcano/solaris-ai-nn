"""Pilot-2 weekly review: grounding trend, reliability trend, limitations."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot2 import Pilot2WeeklyReviewBuilder


def _rollups(scores):
    return [{"grounding_score": s, "reliable_source_count": 1 + i,
             "new_sensory_proto_symbols": s * 10,
             "provenance_completeness": 1.0}
            for i, s in enumerate(scores)]


def test_grounding_trend_included(tmp_path):
    builder = Pilot2WeeklyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollups([0.1, 0.2, 0.4]))
    assert review.grounding_quality_trend == "rising"
    paths = builder.save(review)
    assert os.path.exists(paths["markdown"])


def test_source_reliability_trend_included(tmp_path):
    builder = Pilot2WeeklyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollups([0.1, 0.1, 0.1]))
    md = builder.render_markdown(review)
    assert "source reliability trend" in md


def test_limitations_included(tmp_path):
    builder = Pilot2WeeklyReviewBuilder(base_dir=str(tmp_path))
    review = builder.build(1, _rollups([0.1, 0.1]))
    assert review.limitations
    assert "## Limitations" in builder.render_markdown(review)


def test_overload_signal_changes_recommendation(tmp_path):
    builder = Pilot2WeeklyReviewBuilder(base_dir=str(tmp_path))
    rollups = [{"event_count": 100, "malformed_events": 80,
                "grounding_score": 0.1}]
    review = builder.build(1, rollups)
    assert review.overload_signal is True
    assert review.next_week_exposure_recommendation == "increase_quiet_windows"
