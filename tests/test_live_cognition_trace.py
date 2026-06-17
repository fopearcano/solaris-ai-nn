"""Live cognition trace: serializes, preserves evidence, not proof of reasoning."""

from __future__ import annotations

from solaris_ai_nn.live_cognition import (
    CognitionTraceStatus,
    LiveCognitionTrace,
)


def _trace():
    t = LiveCognitionTrace(trace_id="t1", kind="anticipation",
                           linked_sign_ids=["s1"], linked_concept_ids=["c1"])
    t.uncertainty_state = {"uncertainty": 0.3}
    t.add_support("c1", kind="concept", detail="linked concept")
    t.add_counter("e9", reason="divergent later event")
    return t


def test_trace_serializes():
    d = _trace().to_dict()
    assert d["trace_id"] == "t1"
    assert d["kind"] == "anticipation"
    assert d["linked_sign_ids"] == ["s1"]


def test_evidence_and_counterevidence_preserved():
    d = _trace().to_dict()
    assert d["supporting_count"] == 1
    assert d["counter_count"] == 1
    assert d["contradicting_evidence"][0]["reason"] == "divergent later event"


def test_trace_not_proof_of_reasoning():
    t = _trace()
    assert "not proof of reasoning" in t.to_dict()["note"]
    assert t.status == CognitionTraceStatus.EMERGING
    assert t.promoted is False
    t.status = CognitionTraceStatus.USEFUL
    assert t.promoted is True


def test_uncertainty_accessor():
    assert abs(_trace().uncertainty - 0.3) < 1e-9
