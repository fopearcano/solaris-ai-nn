"""Tests for checkpoint repair."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.checkpoint_repair import (
    CheckpointRepairManager,
)


def test_detects_inconsistent_lineage():
    mgr = CheckpointRepairManager()
    report = mgr.inspect({"checkpoints": {"lineage": [
        {"checkpoint_id": "c1", "timestamp": 100},
        {"checkpoint_id": "c2", "timestamp": 50}]}})
    assert any("impossible_timestamp_order" in i for i in report["issues"])


def test_marks_suspect_checkpoint():
    mgr = CheckpointRepairManager()
    mgr.propose({"checkpoints": {"lineage": [
        {"checkpoint_id": "c1", "timestamp": 100},
        {"checkpoint_id": "c2", "timestamp": 50}]}})
    assert mgr.suspect_checkpoints


def test_identity_mismatch_requests_review_not_rewrite():
    mgr = CheckpointRepairManager()
    actions = mgr.propose({"checkpoints": {"lineage": [
        {"checkpoint_id": "c1", "timestamp": 1, "identity_mismatch": True}]}})
    # Identity mismatch -> operator review, never a silent rewrite.
    assert any(a.action_type == "generate_operator_review_request"
               for a in actions)
    assert mgr.review_requests


def test_incomplete_checkpoint_detected():
    mgr = CheckpointRepairManager()
    report = mgr.inspect({"checkpoints": {"lineage": [
        {"checkpoint_id": "c1", "timestamp": 1, "incomplete": True}]}})
    assert any("incomplete" in i for i in report["issues"])


def test_clean_lineage_no_issues():
    mgr = CheckpointRepairManager()
    report = mgr.inspect({"checkpoints": {"lineage": [
        {"checkpoint_id": "c1", "timestamp": 1},
        {"checkpoint_id": "c2", "timestamp": 2}]}})
    assert report["issues"] == []
