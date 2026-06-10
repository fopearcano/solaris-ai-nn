"""Tests for the cautious scorecard."""

from __future__ import annotations

from solaris_ai_nn.evaluation.scoring import EvaluationScore, score_from_metrics


def test_scores_are_bounded_or_none():
    score = score_from_metrics({
        "continuity": {"heartbeat_count": 10, "unexpected_deaths": 0,
                       "heartbeat_jitter_estimate": 0.0},
        "reactivity": {"stimulus_count": 10, "reaction_count": 10,
                       "avg_signal_to_suggestion_latency_s": 0.001},
        "adaptation": {"prediction_error_start": 1.0,
                       "prediction_error_end": 0.5,
                       "prediction_error_trend": "improving",
                       "readout_update_count": 10,
                       "feedback_alignment_score": None},
    })
    for name, ds in score.domains.items():
        assert ds.score is None or 0.0 <= ds.score <= 1.0, name
        assert ds.explanation  # mandatory


def test_no_consciousness_score_exists():
    score = score_from_metrics({})
    names = " ".join(score.domains.keys()).lower() + " " + score.note.lower()
    assert "consciousness" not in " ".join(score.domains.keys()).lower()
    assert "agi" not in " ".join(score.domains.keys()).lower()
    # The note explicitly disclaims it.
    assert "no consciousness" in score.note.lower()


def test_insufficient_data_gives_none_with_reason():
    score = score_from_metrics({})
    adaptation = score.domains["adaptation_score"]
    assert adaptation.score is None
    assert "insufficient" in adaptation.explanation.lower()
    habit = score.domains["habit_score"]
    assert habit.score is None and habit.explanation


def test_table_renders():
    table = score_from_metrics({}).table()
    assert table.startswith("| domain | score | explanation |")
    assert "n/a" in table
