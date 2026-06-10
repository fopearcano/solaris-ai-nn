"""Tests for the declared action space."""

from __future__ import annotations

import pytest

from solaris_ai_nn.embodiment.action_space import (
    ACTION_SPACE,
    ALLOWED_ACTIONS,
    FORBIDDEN_ACTIONS,
    get_action,
)
from solaris_ai_nn.embodiment.safety import EmbodimentSafety

REQUIRED = ["move_north", "move_south", "move_east", "move_west", "look",
            "rest", "approach_signal", "avoid_signal", "touch_object",
            "emit_ping"]


def test_contains_required_actions():
    for name in REQUIRED:
        assert name in ACTION_SPACE
        assert name in ALLOWED_ACTIONS


def test_action_costs_defined():
    for name in REQUIRED:
        spec = get_action(name)
        assert spec.energy_cost >= 0.0
        assert isinstance(spec.expected_consequence, str) and spec.expected_consequence


def test_forbidden_action_is_rejected():
    assert "leave_simulation" in FORBIDDEN_ACTIONS
    safety = EmbodimentSafety()
    report = safety.validate_action("leave_simulation")
    assert not report.safe
    assert any("forbidden" in v for v in report.violations)


def test_undeclared_action_raises_keyerror():
    with pytest.raises(KeyError):
        get_action("fly_to_the_moon")


def test_preconditions_listed():
    assert "not_exhausted" in get_action("move_north").preconditions
    assert get_action("rest").preconditions == []
