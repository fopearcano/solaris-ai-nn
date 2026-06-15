"""Rhythm + invariant detection: signatures and candidates; provenance kept."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import InvariantDetector, RhythmDetector


def test_rhythm_signature_detected():
    det = RhythmDetector(min_cycles=3, regularity_threshold=0.6)
    for t in range(6):
        det.observe("rf", "radio_frequency", float(t))  # period 1.0, regular
    sig = det.detect("rf")
    assert sig is not None
    assert abs(sig.period - 1.0) < 0.2
    assert sig.regularity >= 0.6
    assert sig.provenance["source_id"] == "rf"


def test_irregular_timing_no_rhythm():
    det = RhythmDetector(min_cycles=3, regularity_threshold=0.8)
    for t in (0.0, 0.5, 3.0, 3.2, 10.0):
        det.observe("rf", "radio_frequency", t)
    assert det.detect("rf") is None


def test_invariant_candidate_detected():
    det = InvariantDetector(min_support=2)
    cand = None
    for _ in range(3):
        cand = det.observe_feature_bucket("rf", "radio_frequency",
                                          "repeated_burst", "power~0.7")
    assert cand is not None
    assert cand.support >= 2
    assert cand.is_strong  # support reached 3


def test_invariant_provenance_preserved():
    det = InvariantDetector(min_support=2)
    for _ in range(2):
        cand = det.observe_feature_bucket("echo", "ultrasound_echo",
                                          "repeating_boundary", "b~3")
    assert cand.provenance["source_id"] == "echo"
    assert cand.modality == "ultrasound_echo"
