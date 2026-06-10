"""Tests for the post-run review."""

from __future__ import annotations

import inspect

import pytest

from solaris_ai_nn.governance import review as R
from solaris_ai_nn.governance.review import (
    NextRunRecommendation,
    PostRunReview,
    ReviewRecord,
)


def test_review_summarizes_incidents():
    incidents = [
        {"type": "health_warning", "severity": "warning"},
        {"type": "checkpoint_failure", "severity": "critical"},
    ]
    record = PostRunReview(run_id="r1", reviewer="alice").build(
        status={"health": {"level": "warning"},
                "manifest": {"mode": "bounded"}},
        incidents=incidents)
    assert record.summary["incident_count"] == 2
    assert record.summary["critical_incidents"] == 1
    assert record.summary["unexplained_failures"] == 1
    assert record.reviewer == "alice"


def test_recommendation_generated_for_each_situation():
    review = PostRunReview(run_id="r1")
    clean = review.build(status={"health": {"level": "ok"}})
    assert clean.recommendation == NextRunRecommendation.EXTEND_DURATION

    investigate = review.build(status={"health": {"level": "critical"}})
    assert investigate.recommendation \
        == NextRunRecommendation.INVESTIGATE_FAILURE

    emergency = review.build(status={"health": {"level": "ok"}},
                             emergency_stop_used=True)
    assert emergency.recommendation \
        == NextRunRecommendation.INVESTIGATE_FAILURE

    reduced = review.build(status={"health": {"level": "ok"}},
                           policy_violations=[{"rule_id": "x"}])
    assert reduced.recommendation == NextRunRecommendation.REDUCE_SCOPE

    stop = review.build(status={"health": {"level": "ok"}}, failure_streak=3)
    assert stop.recommendation == NextRunRecommendation.STOP_LINE_OF_WORK

    repeat = review.build(status={"health": {"level": "warning"}},
                          incidents=[{"type": "health_warning",
                                      "severity": "warning"}])
    assert repeat.recommendation == NextRunRecommendation.REPEAT


def test_rollback_recommendations_for_bad_plasticity():
    record = PostRunReview(run_id="r1").build(
        status={"health": {"level": "critical"}},
        plasticity_changes={"applied_count": 2, "rejected_count": 4,
                            "rollback_count": 0})
    recs = record.summary["rollback_recommendations"]
    assert len(recs) == 2
    assert any("rollback_last" in r for r in recs)


def test_no_automatic_escalation():
    """The review recommends; it never acts. Structurally: the module has no
    way to stop, restart, approve, or mutate anything."""
    source = inspect.getsource(R)
    for verb in ("request_shutdown", "perform_shutdown", "os.", "subprocess",
                 "approve(", "apply(", "rollback("):
        assert verb not in source, verb
    record = PostRunReview(run_id="r1").build(emergency_stop_used=True)
    assert isinstance(record.recommendation, str)  # a string, not an action


def test_record_serializes_and_renders():
    record = PostRunReview(run_id="r1").build(
        status={"health": {"level": "ok"}}, notes=["all quiet"])
    data = record.to_dict()
    assert data["run_id"] == "r1" and data["review_id"]
    md = record.to_markdown()
    assert "Post-run review" in md
    assert "never an automatic action" in md
    assert "all quiet" in md


def test_invalid_recommendation_rejected():
    with pytest.raises(ValueError):
        ReviewRecord(run_id="r1", recommendation="panic")
