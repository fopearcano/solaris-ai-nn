"""Tests for the decision trace recorder."""

from __future__ import annotations

import json

from solaris_ai_nn.executive.coordinator import ExecutiveLayer
from solaris_ai_nn.homeostasis.desire_synthesis import DesireCandidate


def _desires():
    return [DesireCandidate(proposal="rest", motivation=0.6,
                            confidence=0.6,
                            source_needs=["restore_energy"]),
            DesireCandidate(proposal="explore_safely", motivation=0.8,
                            confidence=0.5, blocked=True,
                            blocked_reason="safety beats curiosity")]


def test_records_desires_candidates_scores_selection(tmp_path):
    layer = ExecutiveLayer(state_dir=tmp_path)
    layer.decide(_desires(), context={}, step=7,
                 readout_suggestion="look")
    event = layer.recorder.trace.last()
    assert "rest" in event.input_desires
    assert "rest" in event.candidates and "look" in event.candidates
    assert event.selected is not None
    assert event.scores  # the full score table travels with the event
    assert all("components" in s for s in event.scores)
    assert event.reason
    assert event.step == 7
    assert event.rejected  # everything not selected is on the record


def test_writes_jsonl(tmp_path):
    layer = ExecutiveLayer(state_dir=tmp_path)
    for step in range(3):
        layer.decide(_desires(), context={}, step=step)
    path = tmp_path / "decision_trace.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 3
    assert layer.recorder.rows_written == 3
    for key in ("input_desires", "candidates", "inhibited", "scores",
                "selected", "rejected", "reason", "context_summary",
                "timestamp", "mode"):
        assert key in rows[0], key


def test_inhibited_candidates_included(tmp_path):
    layer = ExecutiveLayer(state_dir=tmp_path)
    layer.decide(_desires(), context={
        "governance_blocks": {"rest": "operator pause"}}, step=1)
    event = layer.recorder.trace.last()
    labels = [row["label"] for row in event.inhibited]
    assert "rest" in labels  # governance-blocked
    assert "explore_safely" in labels  # pre-blocked by homeostasis conflict
    assert all(row["reason"] for row in event.inhibited)


def test_state_and_plan_persist(tmp_path):
    layer = ExecutiveLayer(state_dir=tmp_path, mode="short_plan")
    layer.decide(_desires(), context={}, step=1)
    layer.save_state()
    assert (tmp_path / "executive_state.json").exists()
    state = json.loads((tmp_path / "executive_state.json").read_text())
    assert state["summary"]["enabled"] is True
    if layer.last_plan is not None:
        assert (tmp_path / "current_plan.json").exists()


def test_record_false_skips_disk(tmp_path):
    layer = ExecutiveLayer(state_dir=tmp_path)
    layer.decide(_desires(), context={}, step=1, record=False)
    assert layer.recorder.rows_written == 0
    assert not (tmp_path / "decision_trace.jsonl").exists()
