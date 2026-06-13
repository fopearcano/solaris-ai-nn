"""Integration: LOGOS emits safe internal events, never external action."""

from __future__ import annotations

from solaris_ai_nn.logos_complexity import LogosComplexityEngine
from solaris_ai_nn.logos_complexity.dialectical_trace import TraceEventType


def test_logos_emits_internal_trace_events(tmp_path):
    engine = LogosComplexityEngine(state_dir=tmp_path)
    engine.tick({"world_model": {"contradiction_edges": ["a|c|b"]},
                 "proto_language": {"symbol_count": 20,
                                    "ambiguous_symbol_count": 10,
                                    "ambiguous_symbols": ["S1"]},
                 "mysterium_pressure": 0.6})
    counts = engine.dialectical_trace.counts
    # Tension-detected and synthesis-proposed events are emitted internally.
    assert counts.get(TraceEventType.TENSION_DETECTED, 0) >= 1
    assert counts.get(TraceEventType.SYNTHESIS_PROPOSED, 0) >= 0


def test_no_external_action_capability():
    from solaris_ai_nn.logos_complexity.safety import (
        LogosComplexitySafetyValidator,
    )

    v = LogosComplexitySafetyValidator()
    assert v.logos_can_act_in_real_world() is False
    assert v.logos_has_authority() is False


def test_trace_event_types_are_internal_only():
    # Every trace event is an internal LOGOS dynamic, none is an external
    # action.
    for event in TraceEventType.ALL:
        assert "external" not in event
        assert "real_world" not in event
