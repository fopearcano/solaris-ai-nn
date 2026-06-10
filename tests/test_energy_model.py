"""Tests for the EnergyModel."""

from __future__ import annotations

from solaris_ai_nn.embodiment.energy import EnergyModel


def test_action_consumes_energy():
    e = EnergyModel(max_energy=10.0, energy=10.0)
    assert e.spend(1.0) is True
    assert e.energy == 9.0
    assert e.spent_total == 1.0


def test_rest_restores_energy_bounded():
    e = EnergyModel(max_energy=10.0, energy=5.0, rest_recovery=1.5)
    assert e.rest() == 1.5
    assert e.energy == 6.5
    e.energy = 9.8
    assert abs(e.rest() - 0.2) < 1e-9  # capped at max
    assert e.energy == 10.0


def test_exhaustion_blocks_costly_action():
    e = EnergyModel(energy=0.5, exhaustion_floor=1.0)
    assert e.exhausted
    assert e.can_afford(1.0) is False
    assert e.spend(1.0) is False
    assert e.energy == 0.5  # nothing deducted
    assert e.can_afford(0.0) is True  # zero-cost (rest) still allowed


def test_low_flag_and_snapshot():
    e = EnergyModel(energy=2.5, low_threshold=3.0)
    assert e.is_low
    snap = e.snapshot()
    assert snap["is_low"] is True and snap["exhausted"] is False
    assert "exhaustion_events" in snap


def test_exhaustion_events_counted():
    e = EnergyModel(energy=1.5, exhaustion_floor=1.0)
    e.spend(1.0)  # drops to 0.5 -> crosses the floor
    assert e.exhausted
    assert e.exhaustion_events == 1
