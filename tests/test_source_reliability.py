"""Pilot-2 source reliability: reliable / malformed / unsafe classification."""

from __future__ import annotations

from solaris_ai_nn.pilot2 import ReliabilityClass, SourceReliabilityMonitor


def test_reliable_source_classified():
    mon = SourceReliabilityMonitor()
    for _ in range(5):
        mon.observe_poll("good", success=True, events=10, provenance=10)
    assert mon.record("good").classify() == ReliabilityClass.RELIABLE
    assert "good" in mon.reliable_sources()


def test_malformed_source_classified():
    mon = SourceReliabilityMonitor()
    mon.observe_poll("bad", success=True, events=10, malformed=8)
    assert mon.record("bad").classify() == ReliabilityClass.MALFORMED


def test_unsafe_source_classified():
    mon = SourceReliabilityMonitor()
    mon.observe_poll("evil", success=True, events=10, unsafe=True)
    assert mon.record("evil").classify() == ReliabilityClass.UNSAFE
    assert "evil" in mon.unsafe_sources()


def test_unknown_when_no_data():
    mon = SourceReliabilityMonitor()
    assert mon.record("empty").classify() == ReliabilityClass.UNKNOWN


def test_curation_feedback():
    mon = SourceReliabilityMonitor()
    for _ in range(5):
        mon.observe_poll("good", success=True, events=10, provenance=10)
    mon.observe_poll("evil", success=True, events=5, unsafe=True)
    fb = mon.curation_feedback()
    assert "evil" in fb["disable"]
    assert "good" in fb["keep"]
