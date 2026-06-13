"""Tests for the seasonality (slow drift) model."""

from __future__ import annotations

from solaris_ai_nn.ecology.seasonality import (
    SEASON_ORDER,
    SeasonalityModel,
)


def test_four_seasons_in_order():
    assert SEASON_ORDER == ("spring", "summer", "autumn", "winter")


def test_season_advances_on_interval():
    model = SeasonalityModel(shift_interval=10)
    assert model.season_at(0) == "spring"
    assert model.season_at(10) == "summer"
    assert model.season_at(20) == "autumn"
    assert model.season_at(40) == "spring"  # wraps


def test_update_reports_shift_once():
    model = SeasonalityModel(shift_interval=10)
    shifts = 0
    for step in range(40):
        _, shifted = model.update(step)
        if shifted:
            shifts += 1
    assert shifts == len(model.shifts)
    assert shifts >= 3


def test_profile_multipliers_present():
    model = SeasonalityModel()
    for season in SEASON_ORDER:
        profile = model.profile(season)
        assert set(profile) == {"absence_mult", "novelty_mult",
                                "danger_mult", "reward_mult",
                                "delay_steps"}


def test_winter_sparser_than_spring():
    model = SeasonalityModel()
    winter = model.profile("winter")
    spring = model.profile("spring")
    assert winter["absence_mult"] > spring["absence_mult"]
    assert spring["novelty_mult"] > winter["novelty_mult"]


def test_drift_is_deterministic():
    a = SeasonalityModel(shift_interval=7)
    b = SeasonalityModel(shift_interval=7)
    for step in range(60):
        assert a.season_at(step) == b.season_at(step)
