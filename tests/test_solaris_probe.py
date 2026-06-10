"""Tests for the duck-typed Solaris runtime probe."""

from __future__ import annotations

from solaris_ai_nn.experiments.solaris_sidecar_observation import FakeConscience
from solaris_ai_nn.integration.compatibility import (
    BUS_OBSERVABLE,
    MINIMAL,
    SIDECAR_READY,
    UNAVAILABLE,
)
from solaris_ai_nn.integration.solaris_probe import SolarisRuntimeProbe


def test_fake_compatible_conscience_is_detected():
    report = SolarisRuntimeProbe().probe(FakeConscience())
    assert report.has("bus")
    assert report.has("stimulate") and report.has("react") and report.has("snapshot")
    assert report.has("bus.subscribe_all") and report.has("bus.publish")
    # Real signal classes are not importable here, so sidecar_ready (not full).
    assert report.level == SIDECAR_READY
    assert report.is_compatible(BUS_OBSERVABLE)


def test_missing_bus_is_reported():
    class NoBus:
        def stimulate(self): ...
        def react(self): ...
        def snapshot(self): return {}

    report = SolarisRuntimeProbe().probe(NoBus())
    assert not report.has("bus")
    assert "bus" in report.missing_features()
    assert report.level == MINIMAL
    assert not report.is_compatible(BUS_OBSERVABLE)


def test_none_is_unavailable():
    probe = SolarisRuntimeProbe()
    report = probe.probe(None)
    assert report.level == UNAVAILABLE
    assert not probe.is_compatible()


def test_bus_only_object_is_bus_observable():
    class JustBus:
        class _Bus:
            def subscribe_all(self, h): ...
            def publish(self, s): ...
        bus = _Bus()

    report = SolarisRuntimeProbe().probe(JustBus())
    assert report.level == BUS_OBSERVABLE


def test_to_dict_and_missing_features():
    probe = SolarisRuntimeProbe()
    probe.probe(FakeConscience())
    d = probe.to_dict()
    assert d["level"] == SIDECAR_READY
    assert isinstance(d["features"], list)
    assert "missing" in d
    # FakeConscience exposes everything except real signal classes.
    assert "bus" not in probe.missing_features()


def test_bus_subscriptions_inspected():
    conscience = FakeConscience()
    conscience.bus.subscribe(str, lambda s: None)  # one typed subscription
    report = SolarisRuntimeProbe().probe(conscience)
    assert report.bus_subscriptions.get("str") == 1
