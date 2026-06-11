"""Tests for need memory persistence."""

from __future__ import annotations

import json

from solaris_ai_nn.homeostasis.need_memory import NeedMemory, NeedTrace
from solaris_ai_nn.homeostasis.regulation import HomeostaticRegulator


def test_need_trace_writes_jsonl(tmp_path):
    memory = NeedMemory(tmp_path)
    memory.record(NeedTrace(step=5, dominant_need="restore_energy",
                            dominant_drive="energy_drive", need_count=2,
                            best_desire="rest", valence_rolling=-0.2,
                            being_pressure=0.8, not_being_pressure=0.1,
                            tension=0.1, action_implication="rest"))
    rows = [json.loads(line) for line in
            (tmp_path / "need_trace.jsonl").read_text().splitlines()]
    assert rows[0]["dominant_need"] == "restore_energy"
    assert rows[0]["best_desire"] == "rest"
    assert memory.traces() == rows


def test_homeostasis_state_persists(tmp_path):
    regulator = HomeostaticRegulator(state_dir=tmp_path)
    regulator.update({"embodiment": {"energy": 1.0, "max_energy": 10.0,
                                     "exhausted": True}})
    regulator.save_state()
    assert (tmp_path / "homeostasis_state.json").exists()
    loaded = NeedMemory(tmp_path).load_state()
    assert loaded["summary"]["dominant_need"] == "restore_energy"
    assert "variables" in loaded and "drives" in loaded


def test_auto_determination_persists(tmp_path):
    regulator = HomeostaticRegulator(state_dir=tmp_path)
    regulator.update({"health_level": "critical",
                      "critical_incident": True})
    regulator.save_state()
    data = json.loads((tmp_path / "auto_determination.json").read_text())
    assert data["current"]["not_being_pressure"] > 0
    assert data["shutdown_recommendations"] >= 1


def test_every_update_appends_a_trace_row(tmp_path):
    regulator = HomeostaticRegulator(state_dir=tmp_path)
    for step in range(4):
        regulator.update({"step": step,
                          "embodiment": {"energy": 2.0,
                                         "max_energy": 10.0,
                                         "exhausted": False}})
    memory = regulator.memory
    assert memory.rows_written == 4
    assert len(memory.traces()) == 4
    snap = memory.snapshot()
    assert snap["paths"]["need_trace"].endswith("need_trace.jsonl")
