"""Tests for deterministic templates."""

from __future__ import annotations

from solaris_ai_nn.language.templates import TEMPLATES, render


def test_templates_are_deterministic():
    a = render("action_suggested", action="rest", confidence=0.5)
    b = render("action_suggested", action="rest", confidence=0.5)
    assert a == b
    assert a == ("The readout suggested rest with confidence 0.5. This is a "
                 "tendency, not a committed decision.")


def test_missing_fields_render_as_unknown():
    text = render("signal_received", signal_type="Stimulus")
    assert "unknown" in text  # origin/intensity absent -> 'unknown'
    assert "Stimulus" in text


def test_none_values_render_as_unknown():
    text = render("action_blocked", action="move_north", reason=None)
    assert "because unknown" in text


def test_unknown_template_is_safe():
    text = render("no_such_template", x=1)
    assert "does not know" in text


def test_required_templates_exist():
    for name in ("signal_received", "substrate_updated", "action_suggested",
                 "action_blocked", "reaction_feedback", "habit_reinforced",
                 "synthesis_pruned", "continuity_gap"):
        assert name in TEMPLATES
