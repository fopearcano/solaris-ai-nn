"""PerceptualEnergyBudget: allocates; exhaustion degrades; priority first."""

from __future__ import annotations

from solaris_ai_nn.perceptual_metabolism import PerceptualEnergyBudget
from solaris_ai_nn.perceptual_metabolism.energy_budget import (
    PRIORITY_TASKS,
    TASKS,
)


def test_budget_allocates():
    result = PerceptualEnergyBudget(budget_per_tick=100.0).allocate(list(TASKS))
    assert result.spent > 0
    assert not result.exhausted
    assert all(a.granted > 0 for a in result.allocations)


def test_budget_exhaustion_degrades_gracefully():
    result = PerceptualEnergyBudget(budget_per_tick=3.0).allocate(list(TASKS))
    assert result.exhausted or result.deferred_tasks
    assert result.deferred_tasks  # some tasks deferred, not crashed


def test_safety_continuity_prioritized():
    # With a tiny budget, the priority tasks are funded first.
    result = PerceptualEnergyBudget(budget_per_tick=3.0).allocate(
        ["proto_symbol_candidate_generation", "latent_replay",
         "receptor_update", "sensory_field_update", "absence_detection"])
    granted = {a.task for a in result.allocations if a.granted > 0}
    for task in PRIORITY_TASKS:
        assert task in granted


def test_budget_metaphor_note():
    note = PerceptualEnergyBudget().to_dict()["note"]
    assert "not biological energy" in note
