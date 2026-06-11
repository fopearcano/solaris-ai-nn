"""Tests for autobiographical memory."""

from __future__ import annotations

import json

import pytest

from solaris_ai_nn.developmental.autobiographical_memory import (
    AutobiographicalMemory,
)


def test_event_writes_jsonl(tmp_path):
    memory = AutobiographicalMemory(state_dir=tmp_path)
    memory.add("Runtime survived 24h equivalent.",
               evidence=["runtime_hours=25"], category="survival")
    memory.add("First stable habit formed.",
               evidence=["stable_habit_count=1"], category="habit")
    path = tmp_path / "autobiographical_memory.jsonl"
    assert path.exists()
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 2
    assert rows[0]["category"] == "survival"
    assert rows[0]["evidence_refs"] == ["runtime_hours=25"]


def test_no_first_person_claims():
    memory = AutobiographicalMemory()
    for text in ("I survived a whole day.", "I remember the gap.",
                 "I grew three habits.", "I am developing nicely."):
        with pytest.raises(ValueError, match="first-person"):
            memory.add(text, evidence=["e"])
    # Observational voice is fine.
    event = memory.add("Restart gap detected and identity continuity "
                       "restored.", evidence=["gap_s=12"])
    assert event.text.startswith("Restart gap")


def test_evidence_required():
    memory = AutobiographicalMemory()
    with pytest.raises(ValueError, match="evidence"):
        memory.add("Runtime survived 24h equivalent.", evidence=[])


def test_simulated_vs_real_time_recorded(tmp_path):
    memory = AutobiographicalMemory(state_dir=tmp_path)
    memory.add("Runtime survived 24h equivalent.",
               evidence=["runtime_hours=25"], simulated=True)
    memory.add("Checkpoint completed.",
               evidence=["checkpoint:1"], simulated=False)
    snapshot = memory.snapshot()
    assert snapshot["simulated_events"] == 1
    assert snapshot["real_time_events"] == 1
    rows = [json.loads(line) for line in
            (tmp_path / "autobiographical_memory.jsonl")
            .read_text().splitlines()]
    assert rows[0]["simulated"] is True
    assert rows[1]["simulated"] is False


def test_bounded_and_story():
    memory = AutobiographicalMemory(max_events=3)
    for i in range(5):
        memory.add(f"Checkpoint {i} completed.",
                   evidence=[f"checkpoint:{i}"])
    assert len(memory.events) == 3
    assert "Checkpoint 4 completed." in memory.as_story()
