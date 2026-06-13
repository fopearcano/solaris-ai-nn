"""Tests for the active attention controller."""

from __future__ import annotations

from solaris_ai_nn.active_perception.attention_control import (
    ActiveAttentionController,
)
from solaris_ai_nn.active_perception.salience import SalienceCategory


def test_selects_high_salience_focus():
    ctrl = ActiveAttentionController()
    focus = ctrl.select_focus({"mysterium_pressure": 0.8, "step": 0})
    assert focus.target_ref == "unknown"


def test_emergency_focus_overrides():
    ctrl = ActiveAttentionController()
    ctrl.select_focus({"mysterium_pressure": 0.8, "step": 0})
    focus = ctrl.select_focus({"mysterium_pressure": 0.9, "emergency": True,
                               "step": 1})
    assert focus.emergency is True
    assert focus.category == SalienceCategory.SAFETY


def test_hold_and_release_focus():
    ctrl = ActiveAttentionController()
    ctrl.select_focus({"mysterium_pressure": 0.8, "step": 0})
    ctrl.hold_focus(5)
    assert ctrl.state.current.held_until_step >= 5
    ctrl.release_focus("done")
    assert ctrl.state.current is None


def test_shift_count_tracks_changes():
    ctrl = ActiveAttentionController()
    ctrl.select_focus({"mysterium_pressure": 0.8, "step": 0})
    ctrl.select_focus({"world_model": {"graph_node_count": 5,
                                       "unknown_node_count": 2,
                                       "low_confidence_nodes": ["n1"]},
                       "step": 1})
    assert ctrl.state.shifts_total >= 1


def test_snapshot_shape():
    ctrl = ActiveAttentionController()
    ctrl.select_focus({"mysterium_pressure": 0.5, "step": 0})
    snap = ctrl.snapshot()
    assert "current" in snap and "shifts_total" in snap
