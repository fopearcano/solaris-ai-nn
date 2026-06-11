"""Tests for the consolidation policy."""

from __future__ import annotations

from solaris_ai_nn.developmental.consolidation_policy import (
    ConsolidationPolicy,
    preservation_rank,
)
from solaris_ai_nn.developmental.memory_layers import MemoryLayerManager


def _filled_manager():
    manager = MemoryLayerManager()
    # The important events happen early, then routine traffic ages them
    # out of the recent-hot window -- which is when the ladder matters.
    manager.add_hot({"identity": "anchor mismatch resolved"},
                    kind="identity_continuity", importance=1.0)
    manager.add_hot({"boundary": "violation blocked"},
                    kind="boundary_violation", importance=1.0)
    manager.add_hot({"mysterium": "spike 0.8"},
                    kind="mysterium_spike", importance=0.8)
    for i in range(80):
        manager.add_hot({"step": i}, kind="routine_event")
    return manager


def test_important_events_preserved():
    manager = _filled_manager()
    policy = ConsolidationPolicy(hot_keep_recent=10)
    report = policy.apply(manager)
    assert "identity_continuity" in report.preserved_important
    assert "boundary_violation" in report.preserved_important
    assert "mysterium_spike" in report.preserved_important
    # Identity/safety became fossils; mysterium stayed at high resolution.
    assert report.to_fossil >= 2
    assert manager.state().fossil_count >= 2


def test_compression_report_generated():
    manager = _filled_manager()
    report = ConsolidationPolicy(hot_keep_recent=10).apply(manager)
    assert report.input_count == 83
    assert report.to_warm > 0
    assert report.evidence_summary
    assert 0 < report.compression_ratio < 1.0
    data = report.to_dict()
    assert "preserved_important" in data


def test_raw_evidence_not_silently_deleted():
    manager = _filled_manager()
    before = manager.state().raw_events_seen
    ConsolidationPolicy(hot_keep_recent=10).apply(manager)
    state = manager.state()
    # Everything is accounted for: still hot, summarized, or fossilized.
    assert state.raw_events_seen == before
    accounted = (state.hot_count + state.compressed_events
                 + state.fossil_count)
    assert accounted >= before
    # And every movement carries an evidence summary.
    assert all(m["evidence_summary"] for m in manager.movement_log)


def test_preservation_ladder_ranks():
    from solaris_ai_nn.developmental.memory_layers import MemoryItem

    identity = MemoryItem(layer="hot", kind="identity_continuity")
    routine = MemoryItem(layer="hot", kind="routine_event")
    pruning = MemoryItem(layer="hot", kind="pruning_pass")
    assert preservation_rank(identity) == 1
    assert preservation_rank(pruning) == 7
    assert preservation_rank(routine) == 99
