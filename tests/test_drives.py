"""Tests for the drive resolver."""

from __future__ import annotations

import numpy as np

from solaris_ai_nn.homeostasis.drives import DRIVE_CATEGORIES, DriveResolver
from solaris_ai_nn.homeostasis.needs import NeedEstimator
from solaris_ai_nn.homeostasis.variables import HomeostaticState


def _need_state(**variables):
    state = HomeostaticState()
    for name, value in variables.items():
        state.upsert(name, value)
    return NeedEstimator().estimate(state)


def test_needs_aggregate_into_drives():
    resolver = DriveResolver()
    resolver.aggregate(_need_state(body_energy=0.1, danger_proximity=0.9,
                                   unknown_pressure=0.8))
    drives = resolver.state.drives
    assert drives["energy_drive"].pressure > 0
    assert drives["safety_drive"].pressure > 0
    assert drives["curiosity_drive"].pressure > 0
    assert "restore_energy" in drives["energy_drive"].contributing_needs
    # Safety carries the structural priority bump.
    assert drives["safety_drive"].priority \
        > drives["curiosity_drive"].priority


def test_stale_drives_decay():
    resolver = DriveResolver(decay_factor=0.5)
    resolver.aggregate(_need_state(body_energy=0.1))
    first = resolver.state.drives["energy_drive"].pressure
    assert first > 0
    # No energy need anymore: the drive decays toward zero.
    resolver.aggregate(_need_state(danger_proximity=0.9))
    assert resolver.state.drives["energy_drive"].pressure == first * 0.5
    for _ in range(10):
        resolver.aggregate(_need_state(danger_proximity=0.9))
    assert resolver.state.drives["energy_drive"].pressure == 0.0
    assert resolver.state.drives["energy_drive"].contributing_needs == []


def test_drive_vector_deterministic():
    a = DriveResolver()
    b = DriveResolver()
    need_state = _need_state(body_energy=0.1, danger_proximity=0.9)
    a.aggregate(need_state)
    b.aggregate(need_state)
    assert np.array_equal(a.drive_vector(), b.drive_vector())
    assert len(a.drive_vector()) == len(DRIVE_CATEGORIES) == 10
    assert a.state.to_dict()["vector_order"] == list(DRIVE_CATEGORIES)


def test_desire_bias_and_dominant():
    resolver = DriveResolver()
    resolver.aggregate(_need_state(body_energy=0.05))
    bias = resolver.desire_bias()
    assert bias["rest"] > 0
    assert bias["rest"] > bias.get("reduce_activity", 0.0)
    assert resolver.state.dominant().category == "energy_drive"


def test_drive_conflicts_exposed():
    resolver = DriveResolver()
    resolver.aggregate(_need_state(unknown_pressure=0.9,
                                   danger_proximity=0.9))
    conflicts = resolver.conflicts()
    assert any(set(c["between"]) == {"curiosity_drive", "safety_drive"}
               for c in conflicts)


def test_no_anthropomorphic_language():
    resolver = DriveResolver()
    data = resolver.snapshot()
    assert "not wants" in data["note"]
    import inspect

    from solaris_ai_nn.homeostasis import drives

    source = inspect.getsource(drives).lower()
    for forbidden in ("the system wants", "it feels", "happiness"):
        assert forbidden not in source
