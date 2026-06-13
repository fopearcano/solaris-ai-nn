"""Tests for ecology regimes (profiles, not lesson plans)."""

from __future__ import annotations

import pytest

from solaris_ai_nn.ecology.regimes import (
    EcologyRegime,
    RegimeManager,
    RegimeType,
    get_regime,
)


def test_ten_regime_types():
    assert len(RegimeType.ALL) == 10


def test_every_regime_resolves():
    for name in RegimeType.ALL:
        regime = get_regime(name)
        assert isinstance(regime, EcologyRegime)
        assert regime.expected_pressure  # a pressure, never a correct answer


def test_unknown_regime_rejected():
    with pytest.raises(ValueError):
        get_regime("not_a_regime")


def test_profiles_are_probabilities():
    for name in RegimeType.ALL:
        regime = get_regime(name)
        for attr in ("silence_probability", "pattern_recurrence",
                     "novelty_probability", "anomaly_probability"):
            value = getattr(regime, attr)
            assert 0.0 <= value <= 1.0


def test_sparse_desert_quieter_than_stable():
    sparse = get_regime(RegimeType.SPARSE_DESERT)
    stable = get_regime(RegimeType.STABLE_REPETITION)
    assert sparse.silence_probability > stable.silence_probability
    assert stable.pattern_recurrence > sparse.pattern_recurrence


def test_manager_logs_regime_changes():
    manager = RegimeManager(active_regimes=[RegimeType.MIXED_NURSERY,
                                            RegimeType.SPARSE_DESERT])
    assert manager.current == RegimeType.MIXED_NURSERY
    manager.set_regime(RegimeType.SPARSE_DESERT, step=10, reason="test")
    assert manager.current == RegimeType.SPARSE_DESERT
    assert manager.changes == 1
    # Setting the same regime again does not log a change.
    manager.set_regime(RegimeType.SPARSE_DESERT, step=11)
    assert manager.changes == 1


def test_manager_defaults_to_mixed():
    manager = RegimeManager(active_regimes=[])
    assert manager.current == RegimeType.MIXED_NURSERY
