"""Live prediction assessment: matched/contradicted/ambiguous; failures preserved."""

from __future__ import annotations

from solaris_ai_nn.live_cognition import (
    AnticipationCandidate,
    LivePredictionAssessment,
)


def _ev(sid, channel, absence=False):
    return {"event_id": f"e_{sid}", "timestamp_utc": "2026-06-19T09:00:00Z",
            "source_id": sid, "modality": "scalar", "channel": channel,
            "payload": {"v": 1},
            "quality": {"completeness": 1.0, "noise": 0.0, "is_absence": absence,
                        "is_noisy": False}}


def test_matched_outcome():
    ant = AnticipationCandidate(
        anticipation_id="a1", anticipation_type="recurrence_expected",
        sign_id="s1", linked_concept_ids=["c_machine_body"])
    result = LivePredictionAssessment().assess(
        anticipations=[ant],
        later_events=[_ev("machine_body", "machine_body/load")])
    assert result["live_prediction_matched_count"] >= 1


def test_contradicted_outcome():
    ant = AnticipationCandidate(
        anticipation_id="a1",
        anticipation_type="source_silence_likely_continues", sign_id="s1",
        linked_concept_ids=["c_machine_body"])
    result = LivePredictionAssessment().assess(
        anticipations=[ant],
        later_events=[_ev("machine_body", "machine_body/load")])
    assert result["live_prediction_contradicted_count"] >= 1


def test_ambiguous_outcome():
    ant = AnticipationCandidate(
        anticipation_id="a1", anticipation_type="overload_risk_expected",
        sign_id="s1", linked_concept_ids=["c_machine_body"])
    result = LivePredictionAssessment().assess(
        anticipations=[ant],
        later_events=[_ev("machine_body", "machine_body/load")])
    assert result["ambiguous_count"] >= 1


def test_prediction_failure_preserved():
    # No later events -> not_yet_observed, never forced into success.
    ant = AnticipationCandidate(
        anticipation_id="a1", anticipation_type="recurrence_expected",
        sign_id="s1", linked_concept_ids=["c1"])
    result = LivePredictionAssessment().assess(anticipations=[ant],
                                               later_events=[])
    assert result["not_yet_observed_count"] >= 1
    assert result["live_prediction_matched_count"] == 0
    assert "outcomes" in result
