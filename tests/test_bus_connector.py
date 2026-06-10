"""Tests for the SolarisBusConnector."""

from __future__ import annotations

import pytest

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.experiments.solaris_sidecar_observation import (
    FakeBus,
    Reaction,
    Stimulus,
)
from solaris_ai_nn.integration.bus_connector import SolarisBusConnector
from solaris_ai_nn.integration.suggestion_channel import NeuralSuggestion


def _connector(**kw) -> SolarisBusConnector:
    bridge = SolarisNeuralBridge(action_labels=["approach", "withdraw"], seed=3)
    return SolarisBusConnector(bridge=bridge, **kw)


def test_attaches_to_fake_bus_and_observes():
    bus = FakeBus()
    conn = _connector()
    conn.attach(bus)
    assert conn.active
    bus.publish(Stimulus(payload="light", intensity=0.6))
    assert conn.state.signals_observed == 1
    assert conn.state.signals_by_type.get("Stimulus") == 1
    assert conn.bridge.telemetry.events == 1


def test_reaction_drives_learning():
    bus = FakeBus()
    conn = _connector()
    conn.attach(bus)
    bus.publish(Stimulus(payload="light", intensity=0.6))
    assert conn.bridge.telemetry.readout_updates == 0
    bus.publish(Reaction(valence=1.0))
    assert conn.bridge.telemetry.readout_updates == 1
    assert conn.state.reactions_learned == 1


def test_observe_only_publishes_nothing():
    bus = FakeBus()
    conn = _connector(observe_only=True, suggestion_threshold=0.0)
    conn.attach(bus)
    for i in range(5):
        bus.publish(Stimulus(payload="light", intensity=0.6))
    # Suggestions were produced and stored, but the bus saw only our stimuli.
    assert conn.state.suggestions_produced == 5
    assert conn.state.suggestions_published == 0
    assert all(not isinstance(p, NeuralSuggestion) for p in bus.published)


def test_publishing_mode_publishes_only_suggestions():
    bus = FakeBus()
    conn = _connector(publish_suggestions=True, suggestion_threshold=0.0)
    conn.attach(bus)
    bus.publish(Stimulus(payload="light", intensity=0.6))
    published = [p for p in bus.published if isinstance(p, NeuralSuggestion)]
    assert len(published) == 1
    assert published[0].committed is False
    assert conn.state.suggestions_published == 1
    # Our own suggestion on the bus was NOT re-consumed (no feedback loop).
    assert conn.state.signals_observed == 1


def test_threshold_holds_low_confidence_suggestions():
    bus = FakeBus()
    conn = _connector(suggestion_threshold=2.0)  # impossible bar
    conn.attach(bus)
    bus.publish(Stimulus(payload="light", intensity=0.6))
    assert conn.state.suggestions_produced == 1
    assert conn.state.suggestions_published == 0
    assert "below suggestion threshold" in conn.channel.suggestions[-1].safety_status


def test_allowed_signal_types_filter():
    bus = FakeBus()
    conn = _connector(allowed_signal_types=["Stimulus"])
    conn.attach(bus)
    bus.publish(Stimulus(payload="x"))
    bus.publish(Reaction(valence=1.0))  # filtered out
    assert conn.state.signals_observed == 1
    assert conn.state.reactions_learned == 0


def test_detach_marks_inactive_and_stops_processing():
    bus = FakeBus()
    conn = _connector()
    conn.attach(bus)
    bus.publish(Stimulus(payload="x"))
    conn.detach()
    assert not conn.active
    assert conn.state.attached is False
    bus.publish(Stimulus(payload="y"))  # FakeBus unsubscribed us anyway
    assert conn.state.signals_observed == 1


def test_detach_without_unsubscribe_support():
    class StubbornBus:
        def __init__(self):
            self.handlers = []
        def subscribe_all(self, h):
            self.handlers.append(h)
        def publish(self, s):
            for h in self.handlers:
                h(s)

    bus = StubbornBus()
    conn = _connector()
    conn.attach(bus)
    conn.detach()  # no unsubscribe available -> connector goes inactive
    bus.publish(Stimulus(payload="x"))  # handler still wired, but inactive drops it
    assert conn.state.signals_observed == 0


def test_double_attach_rejected():
    conn = _connector()
    conn.attach(FakeBus())
    with pytest.raises(RuntimeError):
        conn.attach(FakeBus())


def test_snapshot_fields():
    conn = _connector()
    conn.attach(FakeBus())
    snap = conn.snapshot()
    for key in ("active", "observe_only", "state", "channel", "suggestion_threshold"):
        assert key in snap
