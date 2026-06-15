"""BaselineEstimator: learned gradually; shift detected; not overwritten fast."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import BaselineEstimator


def test_baseline_learned_gradually():
    est = BaselineEstimator()
    est.update("rf", "radio_frequency", 1.0)
    est.update("rf", "radio_frequency", 1.0)
    base = est.get("rf")
    assert base is not None
    assert base.sample_count == 2
    assert abs(base.mean_intensity - 1.0) < 1e-6


def test_baseline_not_overwritten_instantly():
    est = BaselineEstimator(learn_rate=0.1)
    for _ in range(6):
        est.update("rf", "radio_frequency", 1.0)
    base = est.get("rf")
    # A single very different sample should not move the mean to the new value.
    est.update("rf", "radio_frequency", 10.0)
    assert base.mean_intensity < 5.0  # nowhere near 10


def test_baseline_shift_detected():
    est = BaselineEstimator(learn_rate=0.3, shift_threshold=0.3)
    for _ in range(8):
        est.update("rf", "radio_frequency", 1.0)
    shift = None
    for _ in range(8):
        s = est.update("rf", "radio_frequency", 5.0)
        shift = shift or s
    assert shift is not None
    assert shift.magnitude >= 0.3


def test_baseline_modality_specific():
    est = BaselineEstimator()
    est.update("rf", "radio_frequency", 1.0)
    est.update("echo", "ultrasound_echo", 5.0)
    assert est.get("rf").modality == "radio_frequency"
    assert est.get("echo").modality == "ultrasound_echo"
