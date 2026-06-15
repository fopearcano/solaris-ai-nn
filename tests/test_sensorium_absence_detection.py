"""AbsenceDetector: missing expected signal -> absence event (stimulus-like)."""

from __future__ import annotations

from solaris_ai_nn.plural_sensorium import AbsenceDetector


def test_missing_expected_signal_creates_absence():
    det = AbsenceDetector(miss_factor=2.0)
    # The signal arrives every ~1s for several ticks.
    for t in range(5):
        det.observe("rf", "radio_frequency", float(t))
    # Then it goes quiet well past the expected interval.
    events = det.check(now=10.0)
    assert events
    assert events[0].source_id == "rf"
    assert events[0].modality == "radio_frequency"


def test_absence_becomes_stimulus_like_event():
    det = AbsenceDetector()
    det.register_expectation("echo", "ultrasound_echo", expected_interval=1.0,
                             last_seen=0.0)
    events = det.check(now=5.0)
    assert events
    ev = events[0]
    # An absence event carries provenance and an elapsed silence -- it is a
    # first-class perceptual event, not the mere lack of one.
    assert ev.provenance["source_id"] == "echo"
    assert ev.elapsed > ev.expected_interval
    assert det.absence_pressure() > 0.0


def test_no_absence_when_signal_present():
    det = AbsenceDetector()
    for t in range(5):
        det.observe("rf", "radio_frequency", float(t))
    # Checked right after the last observation: not overdue yet.
    events = det.check(now=4.5)
    assert events == []
