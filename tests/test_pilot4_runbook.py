"""Pilot4PlanningRunbookBuilder: runbook generated; warnings; planning-only."""

from __future__ import annotations

import os

from solaris_ai_nn.pilot4_planning.operator_runbook import (
    FORBIDDEN,
    WARNINGS,
    Pilot4PlanningRunbookBuilder,
)


def test_runbook_generated(tmp_path):
    path = Pilot4PlanningRunbookBuilder(base_dir=str(tmp_path)).write()
    assert os.path.exists(path) and path.endswith("OPERATOR_RUNBOOK.md")


def test_warnings_included():
    text = Pilot4PlanningRunbookBuilder().render().lower()
    joined = " ".join(WARNINGS).lower()
    assert "do not connect devices" in joined
    assert "do not treat planning as approval" in joined
    assert "do not claim consciousness/agency" in joined
    assert "what not to connect" in text


def test_planning_only_stated():
    text = Pilot4PlanningRunbookBuilder().render().lower()
    assert "planning-only" in text
    assert "plans the door; it does not open it" in text


def test_forbidden_actions_listed():
    joined = " ".join(FORBIDDEN).lower()
    for item in ("real-world actuation", "device", "robotics", "network",
                 "hardware", "shell command"):
        assert item in joined


def test_verify_no_actuation_section():
    text = Pilot4PlanningRunbookBuilder().render().lower()
    assert "how to verify no actuation is enabled" in text
