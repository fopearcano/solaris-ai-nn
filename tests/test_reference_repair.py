"""Tests for reference repair."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.reference_repair import (
    ReferenceRepairManager,
)


def test_broken_reference_detected():
    mgr = ReferenceRepairManager()
    broken = mgr.find_broken({"references": {"broken": ["ref_x"]}})
    assert broken
    assert broken[0]["ref"] == "ref_x"


def test_deterministic_repair_works():
    mgr = ReferenceRepairManager()
    actions = mgr.propose({"references": {"broken_detail": [
        {"ref": "r1", "candidates": ["target_a"]}]}})
    assert any(a.action_type == "repair_broken_reference" for a in actions)
    assert "r1" in mgr.repaired


def test_ambiguous_repair_stays_ambiguous():
    mgr = ReferenceRepairManager()
    actions = mgr.propose({"references": {"broken_detail": [
        {"ref": "r2", "candidates": ["a", "b"]}]}})
    assert any(a.action_type == "mark_world_edge_ambiguous" for a in actions)
    assert "r2" in mgr.ambiguous


def test_dangling_reference_quarantined_not_invented():
    mgr = ReferenceRepairManager()
    actions = mgr.propose({"references": {"broken_detail": [
        {"ref": "r3", "candidates": []}]}})
    assert any(a.action_type == "quarantine_corrupt_record" for a in actions)
    assert "r3" in mgr.quarantined


def test_snapshot_shape():
    mgr = ReferenceRepairManager()
    mgr.propose({"references": {"broken_detail": [
        {"ref": "r1", "candidates": ["a"]}]}})
    snap = mgr.snapshot()
    assert snap["repaired_count"] == 1
