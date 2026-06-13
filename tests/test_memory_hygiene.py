"""Tests for memory hygiene."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.memory_hygiene import (
    PROTECTED_KINDS,
    MemoryHygieneManager,
)


def test_memory_bloat_detected():
    mgr = MemoryHygieneManager()
    detected = mgr.detect({"memory": {"over_budget": ["hot"]}})
    assert detected["over_budget"] == ["hot"]


def test_compaction_proposed_with_protected_preserved():
    mgr = MemoryHygieneManager()
    actions = mgr.propose({"memory": {"over_budget": ["hot"]}})
    compact = [a for a in actions if a.action_type == "compact_memory_layer"]
    assert compact
    # The compaction action carries the protected-kinds list (preserved).
    assert compact[0].metadata.get("preserve_protected")


def test_safety_event_not_compacted_away():
    mgr = MemoryHygieneManager()
    assert mgr.can_compact({"kind": "routine_event"}) is True
    assert mgr.can_compact({"kind": "safety_incident"}) is False
    assert mgr.can_compact({"kind": "boundary_violation"}) is False
    assert "milestone" in PROTECTED_KINDS


def test_compression_loss_risk_flagged():
    mgr = MemoryHygieneManager()
    detected = mgr.detect({"memory": {"over_budget": ["hot"],
                                      "compression_ratio": 0.99}})
    assert detected["compression_loss_risk"] is True


def test_consolidation_requested_on_bloat():
    mgr = MemoryHygieneManager()
    actions = mgr.propose({"memory": {"over_budget": ["hot"]}})
    assert any(a.action_type == "request_consolidation" for a in actions)
