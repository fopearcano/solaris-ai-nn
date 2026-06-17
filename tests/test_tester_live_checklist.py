"""Tester live checklist: generated, stop conditions included, no step execution."""

from __future__ import annotations

from solaris_ai_nn.tester_live_readonly import TesterLiveChecklist


def test_checklist_generated():
    c = TesterLiveChecklist.build()
    d = c.to_dict()
    assert d["section_count"] == 4
    titles = [s["title"] for s in d["sections"]]
    assert any("Before live test" in t for t in titles)
    assert any("After live run" in t for t in titles)


def test_stop_conditions_included():
    c = TesterLiveChecklist.build()
    stops = c.stop_conditions()
    assert stops
    assert any("governance" in s.lower() for s in stops)


def test_no_step_execution():
    d = TesterLiveChecklist.build().to_dict()
    assert d["executes_steps"] is False


def test_markdown_marks_stop():
    md = TesterLiveChecklist.build().to_markdown()
    assert "STOP" in md
    assert "# Tester Live-Read-Only Checklist" in md
