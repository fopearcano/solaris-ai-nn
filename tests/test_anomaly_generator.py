"""Tests for the ecology anomaly generator (perturbations, not errors)."""

from __future__ import annotations

import random

from solaris_ai_nn.ecology.anomalies import AnomalyGenerator, AnomalyKind


def test_eight_anomaly_kinds():
    assert len(AnomalyKind.ALL) == 8


def test_anomalies_are_never_errors():
    gen = AnomalyGenerator(rng=random.Random(2))
    produced = 0
    for step in range(200):
        anomaly = gen.maybe_anomaly(step, probability=0.3)
        if anomaly is not None:
            produced += 1
            assert anomaly["is_error"] is False
            assert anomaly["novelty_hint"] == 0.9
    assert produced > 0


def test_anomaly_rate_bounded_by_probability():
    gen = AnomalyGenerator(rng=random.Random(2))
    # Probability is internally clamped to <= 0.5.
    for step in range(100):
        gen.maybe_anomaly(step, probability=10.0)
    assert len(gen.anomalies) <= 100


def test_anomaly_count_capped():
    gen = AnomalyGenerator(rng=random.Random(2), max_anomalies=5)
    for step in range(500):
        gen.maybe_anomaly(step, probability=0.5)
    assert len(gen.anomalies) == 5
    assert gen.capped > 0


def test_established_pattern_biases_sequence_break():
    gen = AnomalyGenerator(rng=random.Random(5))
    kinds = set()
    for step in range(100):
        anomaly = gen.maybe_anomaly(step, probability=0.5,
                                    established_pattern="pattern_a")
        if anomaly:
            kinds.add(anomaly["kind"])
    assert AnomalyKind.SEQUENCE_BREAK in kinds


def test_snapshot_notes_not_errors():
    gen = AnomalyGenerator(rng=random.Random(2))
    gen.maybe_anomaly(0, probability=0.5)
    snap = gen.snapshot()
    assert "not errors" in snap["note"]
