"""SourceHealthMonitor: silent / noisy / corrupt / resumed sources detected."""

from __future__ import annotations

from solaris_ai_nn.live_field import SourceHealthMonitor, SourceHealthState


def test_silent_source_detected():
    mon = SourceHealthMonitor()
    mon.register("rf", expected_silence_window_s=2.0)
    for t in range(3):
        mon.observe_event("rf", float(t))
    events = mon.check_silence(now=10.0)
    assert events
    assert "rf" in mon.silent_sources()


def test_active_source_detected():
    mon = SourceHealthMonitor()
    for t in range(4):
        mon.observe_event("rf", float(t))
    assert "rf" in mon.active_sources()


def test_corrupt_source_detected():
    mon = SourceHealthMonitor()
    mon.observe_event("echo", 1.0, corrupt=True)
    assert "echo" in mon.corrupt_sources()
    assert mon.state_of("echo") == SourceHealthState.CORRUPT


def test_resumed_source_detected():
    mon = SourceHealthMonitor()
    mon.register("rf", expected_silence_window_s=1.0)
    mon.observe_event("rf", 0.0)
    mon.check_silence(now=5.0)  # goes silent
    assert "rf" in mon.silent_sources()
    mon.observe_event("rf", 6.0)  # resumes
    assert mon.state_of("rf") == SourceHealthState.RESUMED


def test_missing_file_reported():
    mon = SourceHealthMonitor()
    ev = mon.report_missing_file("vib", "/x/vib.jsonl")
    assert ev.event_type == "expected_file_missing"
    assert "vib" in mon.silent_sources()
