"""Tests for the delayed-consequence model (cause now, effect later)."""

from __future__ import annotations

import random

from solaris_ai_nn.ecology.delayed_consequence import (
    ConsequenceKind,
    DelayedConsequenceModel,
)


def test_five_consequence_kinds():
    assert len(ConsequenceKind.ALL) == 5


def test_schedule_then_resolve_at_due_step():
    model = DelayedConsequenceModel(rng=random.Random(1))
    record = model.schedule(step=10, kind=ConsequenceKind.REWARD_THEN_POSITIVE,
                            delay=5)
    assert record["due_step"] == 15
    assert record["group_id"].startswith("DLY_")
    # Nothing due before the due step.
    assert model.due_at(14) == []
    due = model.due_at(15)
    assert len(due) == 1
    assert due[0]["group_id"] == record["group_id"]


def test_consequence_carries_group_id_not_label():
    model = DelayedConsequenceModel(rng=random.Random(1))
    record = model.schedule(step=0, kind=ConsequenceKind.BOUNDARY_THEN_DANGER,
                            delay=3)
    # The record links by id and shapes an event type, but supplies no
    # "correct answer" / label key.
    assert "label" not in record
    assert "correct_answer" not in record
    assert record["consequence_type"] == "danger_analogue"


def test_groups_created_and_resolved_counters():
    model = DelayedConsequenceModel(rng=random.Random(1))
    for step in range(5):
        model.schedule(step=step, delay=2)
    assert model.groups_created == 5
    resolved = 0
    for step in range(20):
        resolved += len(model.due_at(step))
    assert model.groups_resolved == resolved == 5


def test_pending_count_tracks_unresolved():
    model = DelayedConsequenceModel(rng=random.Random(1))
    model.schedule(step=0, delay=10)
    model.schedule(step=0, delay=12)
    assert model.pending_count == 2
    model.due_at(10)
    assert model.pending_count == 1


def test_default_kind_chosen_with_rng():
    model = DelayedConsequenceModel(rng=random.Random(1))
    record = model.schedule(step=0)
    assert record["kind"] in ConsequenceKind.ALL
