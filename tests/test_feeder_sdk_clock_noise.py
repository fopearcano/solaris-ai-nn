"""Clock + noise helpers: jitter/dropout reproducible; burst/drift generated."""

from __future__ import annotations

from solaris_ai_nn.feeder_sdk import (
    BurstModel,
    DriftModel,
    DropoutModel,
    FeatureNoiseModel,
    JitterModel,
    TickSchedule,
)


def test_jitter_reproducible():
    a = JitterModel(amplitude=0.3, seed=7)
    b = JitterModel(amplitude=0.3, seed=7)
    assert [a.apply(1.0) for _ in range(5)] == [b.apply(1.0) for _ in range(5)]


def test_dropout_reproducible():
    a = DropoutModel(probability=0.5, seed=7)
    b = DropoutModel(probability=0.5, seed=7)
    assert [a.drop() for _ in range(10)] == [b.drop() for _ in range(10)]


def test_noise_reproducible():
    a = FeatureNoiseModel(sigma=0.1, seed=7)
    b = FeatureNoiseModel(sigma=0.1, seed=7)
    assert [a.apply(0.5) for _ in range(5)] == [b.apply(0.5) for _ in range(5)]


def test_burst_generated():
    burst = BurstModel(probability=1.0, gain=2.0, seed=7)
    assert burst.apply(0.5) == 1.0


def test_drift_accumulates():
    drift = DriftModel(rate=0.1)
    first = drift.apply(0.0)
    second = drift.apply(0.0)
    assert second > first


def test_tick_schedule():
    times = TickSchedule(interval=2.0, count=3).times()
    assert times == [0.0, 2.0, 4.0]
