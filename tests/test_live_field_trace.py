"""LiveFieldTrace: records feeder/source/receptor events; provenance; blocks."""

from __future__ import annotations

import pytest

from solaris_ai_nn.live_field import LiveFieldTrace, LiveFieldTraceEventType


def test_trace_records_feeder_source_receptor_events():
    trace = LiveFieldTrace()
    trace.record(LiveFieldTraceEventType.FEEDER_SEEN, feeder_id="rf_feed")
    trace.record(LiveFieldTraceEventType.SOURCE_HEALTH_CHANGED, source_id="rf",
                 source_health="silent")
    trace.record(LiveFieldTraceEventType.RECEPTOR_UPDATED, tick=1,
                 modality="radio_frequency")
    counts = trace.counts_by_type()
    assert counts[LiveFieldTraceEventType.FEEDER_SEEN] == 1
    assert counts[LiveFieldTraceEventType.RECEPTOR_UPDATED] == 1


def test_provenance_preserved():
    trace = LiveFieldTrace()
    trace.record(LiveFieldTraceEventType.EXTERNAL_EVENT_INGESTED, tick=2,
                 source_id="rf", provenance={"source_id": "rf",
                                             "feeder_id": "rf_feed"})
    ev = trace.of_type(LiveFieldTraceEventType.EXTERNAL_EVENT_INGESTED)[0]
    assert ev.provenance["feeder_id"] == "rf_feed"


def test_safety_block_visible():
    trace = LiveFieldTrace()
    trace.record(LiveFieldTraceEventType.SAFETY_BLOCK,
                 detail="live mode requires governance approval")
    assert trace.count(LiveFieldTraceEventType.SAFETY_BLOCK) == 1


def test_unknown_event_rejected():
    trace = LiveFieldTrace()
    with pytest.raises(ValueError):
        trace.record("not_a_real_live_event")
