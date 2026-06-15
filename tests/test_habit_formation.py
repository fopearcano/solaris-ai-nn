"""HabitFormationEngine: habit forms; bad habit weakens; safety override remains."""

from __future__ import annotations

from solaris_ai_nn.action_reaction import (
    HabitFormationEngine,
    HabitStrength,
    HabitTrigger,
)


def test_habit_candidate_forms():
    engine = HabitFormationEngine()
    h = engine.reinforce(HabitTrigger.SOURCE_SILENCE_REPEATS)
    assert h.reinforcement_count == 1
    assert h.action_kind == "inspect_absence_window"
    assert engine.candidates()


def test_habit_strengthens_then_weakens():
    engine = HabitFormationEngine()
    for _ in range(4):
        engine.reinforce(HabitTrigger.OVERLOAD_RISES)
    assert engine.strengthened()
    engine.weaken(HabitTrigger.OVERLOAD_RISES)
    assert engine.weakened()


def test_safety_override_remains():
    engine = HabitFormationEngine()
    for _ in range(4):
        engine.reinforce(HabitTrigger.SIGN_DRIFT_RISES)
    h = engine.inhibit(HabitTrigger.SIGN_DRIFT_RISES)
    # Safety/governance can always override a habit.
    assert h.inhibited is True
    assert h.strength == 0.0
    assert h.strength_band == HabitStrength.INHIBITED


def test_habit_not_instinct_language():
    engine = HabitFormationEngine()
    h = engine.reinforce(HabitTrigger.BOUNDARY_UNCERTAIN)
    note = h.to_dict()["note"]
    assert "not instinct" in note
    assert "overrideable" in note
