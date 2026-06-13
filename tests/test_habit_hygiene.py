"""Tests for habit hygiene."""

from __future__ import annotations

from solaris_ai_nn.autoregeneration.habit_hygiene import HabitHygieneManager


def test_dead_habit_detected():
    mgr = HabitHygieneManager()
    actions = mgr.propose({"habits": {"dead_habits": ["h1"]}})
    assert any(a.action_type == "retire_dead_habit" for a in actions)


def test_runaway_habit_detected():
    mgr = HabitHygieneManager()
    actions = mgr.propose({"habits": {"runaway_habits": ["h2"]}})
    assert any(a.action_type == "decay_runaway_habit" for a in actions)


def test_safety_habit_not_weakened_without_governance():
    mgr = HabitHygieneManager()
    actions = mgr.propose({"habits": {"runaway_habits": ["avoid_danger"]}})
    safety = [a for a in actions if a.target_ref == "avoid_danger"]
    assert safety
    assert safety[0].requires_governance is True


def test_poor_outcome_loop_requests_stabilization():
    mgr = HabitHygieneManager()
    actions = mgr.propose({"habits": {"poor_outcome_loops": ["h3"]}})
    assert any(a.action_type == "switch_to_stabilization_mode"
               for a in actions)
    assert mgr.stabilization_requests


def test_is_safety_habit():
    assert HabitHygieneManager.is_safety_habit("avoid_danger") is True
    assert HabitHygieneManager.is_safety_habit("look") is False
