"""Tests for the MemoryConsolidator."""

from __future__ import annotations

from solaris_ai_nn.inner_map.model import MemoryState
from solaris_ai_nn.memory.consolidation import MemoryConsolidator
from solaris_ai_nn.memory.trace_memory import TraceMemory


def _trace_with_patterns() -> TraceMemory:
    tm = TraceMemory()
    # Repeated Stimulus events, an absence cycle, actions, and reactions.
    for _ in range(5):
        tm.record_event(0, "Stimulus", payload="light", is_absence=False)
        tm.record_action(0, "approach")
        tm.record_reaction(0, 1.0)
    # Two distinct absence cycles separated by a normal stimulus.
    tm.record_event(0, "Stimulus", payload="I exist!", is_absence=True)
    tm.record_event(0, "Stimulus", payload="I exist!", is_absence=True)
    tm.record_event(0, "Stimulus", payload="light", is_absence=False)
    tm.record_event(0, "Stimulus", payload="I exist!", is_absence=True)
    tm.record_reaction(0, -1.0)
    return tm


def test_counts_repeated_patterns():
    report = MemoryConsolidator().consolidate(_trace_with_patterns())
    assert report.dominant_signal_type == "Stimulus"
    assert report.kind_counts["Stimulus"] >= 5
    assert "Stimulus" in report.repeated_patterns


def test_detects_absence_cycles():
    report = MemoryConsolidator().consolidate(_trace_with_patterns())
    assert report.absence_count == 3
    assert report.absence_cycles == 2  # two separated runs of absence stimuli


def test_counts_reactions_and_stable_action():
    report = MemoryConsolidator().consolidate(_trace_with_patterns())
    assert report.reaction_count == 6
    assert report.positive_reactions == 5
    assert report.negative_reactions == 1
    assert report.stable_action == "approach"
    assert report.stable_action_ratio == 1.0


def test_creates_memory_state():
    consolidator = MemoryConsolidator()
    report = consolidator.consolidate(_trace_with_patterns())
    state = consolidator.to_memory_state(report)
    assert isinstance(state, MemoryState)
    assert state.dominant_recent_signal_type == "Stimulus"
    assert state.recent_absence_count == 3
    assert state.recent_reaction_count == 6
    assert state.consolidated_summaries  # non-empty


def test_window_size_limits_records():
    tm = TraceMemory()
    for i in range(50):
        tm.record_event(i, "Push")
    for i in range(5):
        tm.record_event(i, "Stimulus")
    report = MemoryConsolidator().consolidate(tm, window_size=5)
    assert report.events_considered == 5
    assert report.dominant_signal_type == "Stimulus"  # only the last 5
