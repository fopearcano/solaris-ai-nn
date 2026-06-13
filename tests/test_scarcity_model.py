"""Tests for the ecology scarcity model."""

from __future__ import annotations

from solaris_ai_nn.ecology.scarcity import ScarcityModel


def test_signal_drought_grows_and_resets():
    model = ScarcityModel()
    for _ in range(5):
        model.observe(had_signal=False, had_reward=False,
                      expected_signal=True, in_scarcity_phase=True)
    assert model.signal_drought_steps == 5
    assert model.missing_expected_signals == 5
    model.observe(had_signal=True, had_reward=True,
                  expected_signal=True, in_scarcity_phase=False)
    assert model.signal_drought_steps == 0


def test_resource_level_stays_in_unit_interval():
    model = ScarcityModel()
    for _ in range(100):
        model.observe(had_signal=False, had_reward=False,
                      expected_signal=True, in_scarcity_phase=True)
    assert 0.0 <= model.resource_level <= 1.0
    assert model.resource_level == 0.0  # fully drained eventually
    for _ in range(100):
        model.observe(had_signal=True, had_reward=True,
                      expected_signal=False, in_scarcity_phase=False)
    assert 0.0 <= model.resource_level <= 1.0


def test_pressures_increase_with_drought():
    model = ScarcityModel()
    for _ in range(15):
        model.observe(had_signal=False, had_reward=False,
                      expected_signal=True, in_scarcity_phase=True)
    pressures = model.pressures()
    assert pressures["seek_signal_pressure"] == 1.0
    assert pressures["rest_consolidation_pressure"] > 0.0
    assert 0.0 <= pressures["scarcity_uncertainty_pressure"] <= 1.0


def test_pressures_keys_are_stable():
    model = ScarcityModel()
    model.observe(had_signal=True, had_reward=True,
                  expected_signal=True, in_scarcity_phase=False)
    keys = set(model.pressures())
    assert keys == {"seek_signal_pressure", "reward_scarcity_pressure",
                    "rest_consolidation_pressure",
                    "scarcity_uncertainty_pressure", "resource_level"}
