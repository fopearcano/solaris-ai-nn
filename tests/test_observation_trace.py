"""ObservationTrace: events recorded; before/after preserved; provenance kept."""

from __future__ import annotations

import pytest

from solaris_ai_nn.organismic_demo import ObservationTrace, TraceEventType


def test_trace_events_recorded():
    trace = ObservationTrace()
    trace.record(TraceEventType.EXTERNAL_EVENT_SEEN, tick=1,
                 modality="radio_frequency", source_id="rf")
    trace.record(TraceEventType.RECEPTOR_UPDATED, tick=1, modality="vibration")
    assert trace.count(TraceEventType.EXTERNAL_EVENT_SEEN) == 1
    assert trace.counts_by_type()[TraceEventType.RECEPTOR_UPDATED] == 1


def test_before_after_preserved():
    trace = ObservationTrace()
    trace.record(TraceEventType.RECEPTOR_UPDATED, tick=2,
                 before={"intensity": 0.1}, after={"intensity": 0.9})
    ev = trace.of_type(TraceEventType.RECEPTOR_UPDATED)[0]
    assert ev.before == {"intensity": 0.1}
    assert ev.after == {"intensity": 0.9}


def test_provenance_preserved():
    trace = ObservationTrace()
    trace.record(TraceEventType.EXTERNAL_EVENT_SEEN, tick=3, source_id="rf",
                 provenance={"source_id": "rf", "feeder_trust": "fixture"})
    ev = trace.of_type(TraceEventType.EXTERNAL_EVENT_SEEN)[0]
    assert ev.provenance["source_id"] == "rf"


def test_unknown_event_rejected():
    trace = ObservationTrace()
    with pytest.raises(ValueError):
        trace.record("not_a_real_trace_event")


def test_trace_serializes():
    trace = ObservationTrace()
    trace.record(TraceEventType.ABSENCE_DETECTED, tick=4, modality="vibration")
    data = trace.to_dict()
    assert data["event_count"] == 1
    assert "counts_by_type" in data
