"""Live cognition contamination filter: label/gloss/operator dependency; language."""

from __future__ import annotations

from solaris_ai_nn.live_cognition import (
    LiveCognitionContaminationFilter,
    LiveCognitionTrace,
)


def _trace(tid, limitations=None):
    t = LiveCognitionTrace(trace_id=tid, linked_concept_ids=["c1"])
    t.limitations = limitations or []
    return t


def test_human_label_dependency_detected():
    res = LiveCognitionContaminationFilter().evaluate(
        trace=_trace("t1"), sign_sources={"machine_body": 4},
        sign_contamination=["human_label_dependency"])
    assert "human_label_dependency" in res.types
    assert res.contaminated is True


def test_debug_gloss_dependency_detected():
    res = LiveCognitionContaminationFilter().evaluate(
        trace=_trace("t2"), sign_sources={"machine_body": 4},
        sign_contamination=["debug_gloss_dependency"])
    assert "debug_gloss_dependency" in res.types


def test_operator_phrase_dependency_detected():
    res = LiveCognitionContaminationFilter().evaluate(
        trace=_trace("t3"), sign_sources={"operator_pulse": 5})
    assert "operator_pulse_dominance" in res.types
    assert res.contaminated is True


def test_understanding_claim_blocked():
    res = LiveCognitionContaminationFilter().evaluate(
        trace=_trace("t4"), sign_sources={"machine_body": 4},
        annotations={"debug_alias": "the word means dog and understands"})
    assert "sign_as_language_claim" in res.types
    assert res.contaminated is True
