"""Tests for the MeaningTraceBuilder."""

from __future__ import annotations

from solaris_ai_nn.language.meaning_trace import MeaningTraceBuilder
from solaris_ai_nn.signals import canonical as C


def test_signal_creates_atoms():
    b = MeaningTraceBuilder()
    atoms = b.from_signal(C.Stimulus(payload="light", intensity=0.9,
                                     origin="world"),
                          {"vector_len": 38, "vector_norm": 2.5})
    subjects = [a.subject for a in atoms]
    assert "Stimulus" in subjects
    assert any("intensity" in s for s in subjects)  # high-intensity atom
    assert any(a.predicate == "encoded_as" for a in atoms)
    assert all(a.category == "signal" for a in atoms)


def test_absence_and_reaction_atoms():
    b = MeaningTraceBuilder()
    absence = b.from_signal(C.Stimulus(payload="x", is_absence=True))
    assert any("absence" in a.subject for a in absence)
    reaction = b.from_signal(C.Reaction(valence=-0.8))
    assert any("negative" in str(a.value) for a in reaction)


def test_bridge_snapshot_creates_atoms():
    b = MeaningTraceBuilder()
    atoms = b.from_bridge_snapshot({
        "substrate_type": "esn", "substrate_state_norm": 4.2,
        "last_suggested_action": "approach", "last_confidence": 0.7,
        "habit_pathways": 3})
    predicates = [a.predicate for a in atoms]
    assert "updated" in predicates and "suggested" in predicates


def test_plasticity_result_creates_atoms():
    b = MeaningTraceBuilder()
    applied = b.from_plasticity_result(
        {"status": "applied", "applied": True, "step_id": "abc",
         "old_value": 0.3, "new_value": 0.4})
    assert applied[0].category == "plasticity"
    assert applied[0].predicate == "updated"
    rejected = b.from_plasticity_result(
        {"status": "rejected", "applied": False, "step_id": "x",
         "message": "out of bounds"})
    assert rejected[0].predicate == "blocked"


def test_capacity_and_snapshot():
    b = MeaningTraceBuilder(capacity=5)
    for i in range(10):
        b.append_atoms(b.from_signal(C.Push(intensity=0.1)))
    assert len(b) == 5
    assert b.dropped > 0
    snap = b.snapshot()
    assert snap["atom_count"] == 5
    assert "by_category" in snap and snap["by_category"].get("signal", 0) > 0
    trace = b.to_trace()
    assert trace.to_dict()["atom_count"] == 5
