"""Tests for the dialectical trace."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity.dialectical_trace import (
    DialecticalTrace,
    TraceEventType,
)


def test_trace_writes_jsonl(tmp_path):
    trace = DialecticalTrace(state_dir=tmp_path)
    trace.record(TraceEventType.TENSION_DETECTED, "T1", "known vs unknown")
    assert (tmp_path / "dialectical_trace.jsonl").exists()
    assert trace.snapshot()["event_count"] == 1


def test_synthesis_refused_recorded(tmp_path):
    trace = DialecticalTrace(state_dir=tmp_path)
    trace.record(TraceEventType.SYNTHESIS_REFUSED, "T1", "unsafe")
    assert trace.counts[TraceEventType.SYNTHESIS_REFUSED] == 1


def test_complexity_shift_recorded(tmp_path):
    trace = DialecticalTrace(state_dir=tmp_path)
    trace.record(TraceEventType.COMPLEXITY_SHIFT, "",
                 "productive -> overloaded")
    assert trace.counts[TraceEventType.COMPLEXITY_SHIFT] == 1


def test_unknown_event_rejected(tmp_path):
    import pytest

    from solaris_ai_nn.logos_complexity.dialectical_trace import (
        DialecticalTraceEvent,
    )

    with pytest.raises(ValueError):
        DialecticalTraceEvent(event_type="enlightenment")


def test_twelve_trace_event_types():
    assert len(TraceEventType.ALL) == 12
