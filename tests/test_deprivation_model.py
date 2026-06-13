"""Tests for the bounded deprivation / silence model."""

from __future__ import annotations

import random

from solaris_ai_nn.ecology.deprivation import (
    DeprivationKind,
    DeprivationModel,
)


def test_six_deprivation_kinds():
    assert len(DeprivationKind.ALL) == 6


def test_window_is_bounded_by_max_window():
    model = DeprivationModel(rng=random.Random(1), max_window=8,
                             long_window=20)
    # Force a window to start with certainty.
    model.maybe_start(step=0, silence_probability=1.0)
    length = 0
    while model.step_window() is not None:
        length += 1
        if length > 100:  # guard against an unbounded window bug
            break
    assert length <= 8


def test_after_anomaly_starts_quiet():
    model = DeprivationModel(rng=random.Random(1))
    kind = model.maybe_start(step=0, silence_probability=0.0,
                             after_anomaly=True)
    assert kind == DeprivationKind.POST_ANOMALY_QUIET


def test_no_window_when_probability_zero():
    model = DeprivationModel(rng=random.Random(1))
    assert model.maybe_start(step=0, silence_probability=0.0) is None


def test_active_property_tracks_window():
    model = DeprivationModel(rng=random.Random(1))
    model.maybe_start(step=0, silence_probability=1.0)
    assert model.active is True
    while model.step_window() is not None:
        pass
    assert model.active is False


def test_deprived_steps_counted():
    model = DeprivationModel(rng=random.Random(1), max_window=5)
    model.maybe_start(step=0, silence_probability=1.0)
    while model.step_window() is not None:
        pass
    assert model.deprived_steps > 0
