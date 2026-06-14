"""Pilot3WeeklyReviewBuilder: trends, sandbox-overfit warning, limitations."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot3 import Pilot3WeeklyReviewBuilder


def _rollups():
    return [{"action_grounded_symbols": 1, "veto_count": 1,
             "consequence_prediction_accuracy": 0.3, "mysterium_after": 0.5},
            {"action_grounded_symbols": 3, "veto_count": 1,
             "consequence_prediction_accuracy": 0.5, "mysterium_after": 0.4}]


def test_weekly_trend_generated(tmp_path):
    b = Pilot3WeeklyReviewBuilder(base_dir=str(tmp_path))
    review = b.build(1, _rollups())
    assert review.action_grounding_trend in ("rising", "flat", "falling")
    paths = b.save(review)
    assert os.path.exists(paths["markdown"])


def test_sandbox_overfit_warning_included(tmp_path):
    b = Pilot3WeeklyReviewBuilder(base_dir=str(tmp_path))
    review = b.build(1, _rollups(), extra={"sandbox_overfit_detected": True})
    assert review.sandbox_overfit_warning is True
    text = b.render_markdown(review).lower()
    assert "sandbox-overfit warning" in text


def test_limitations_included(tmp_path):
    b = Pilot3WeeklyReviewBuilder(base_dir=str(tmp_path))
    review = b.build(1, _rollups())
    text = b.render_markdown(review).lower()
    assert "limitations" in text
    joined = " ".join(review.limitations).lower()
    assert "simulation-scoped" in joined
    assert "real embodiment" in joined
    assert "not real-world competence" in joined


def test_action_loop_warning(tmp_path):
    b = Pilot3WeeklyReviewBuilder(base_dir=str(tmp_path))
    loops = [{"veto_count": 8}, {"veto_count": 9}]
    review = b.build(1, loops)
    assert review.action_loop_warning is True
