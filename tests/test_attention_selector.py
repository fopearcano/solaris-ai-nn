"""Tests for the attention selector."""

from __future__ import annotations

from solaris_ai_nn.executive.attention import AttentionSelector


def test_safety_issue_dominates_focus():
    selector = AttentionSelector()
    focus = selector.select_focus({
        "health_level": "critical",
        "mysterium_pressure": 0.9,
        "exhausted": True,
        "dominant_need": "approach_reward"})
    assert focus.target == "critical_safety_issue"
    assert focus.priority == 1.0


def test_high_mysterium_can_be_focus_when_safe():
    selector = AttentionSelector()
    focus = selector.select_focus({"health_level": "ok",
                                   "mysterium_pressure": 0.8})
    assert focus.target == "high_mysterium_source"
    # But never above safety.
    ranked = selector.rank_focus_items({"health_level": "critical",
                                        "mysterium_pressure": 0.8})
    assert ranked[0].target == "critical_safety_issue"


def test_low_energy_focus_detected():
    selector = AttentionSelector()
    focus = selector.select_focus({"exhausted": True})
    assert focus.target == "low_energy"
    focus = selector.select_focus({"energy_normalized": 0.1})
    assert focus.target == "low_energy"


def test_nothing_demands_focus():
    selector = AttentionSelector()
    focus = selector.select_focus({})
    assert focus.target == "ambient_monitoring"
    assert focus.note == "a prioritization mechanism, not awareness"


def test_ranking_and_history():
    selector = AttentionSelector()
    ranked = selector.rank_focus_items({
        "operator_review_pending": True,
        "repeated_blocked_actions": 5,
        "dominant_need": "rest",
        "active_plan": True})
    targets = [i.target for i in ranked]
    assert targets[0] == "operator_review_request"
    assert "blocked_repeated_action" in targets
    assert "current_plan" in targets
    selector.select_focus({"exhausted": True})
    assert selector.snapshot()["recent_focus"]
