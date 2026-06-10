"""Tests for language tracing inside the NeuralBridge."""

from __future__ import annotations

from solaris_ai_nn.bridges.neural_bridge import SolarisNeuralBridge
from solaris_ai_nn.signals import canonical as C


def test_bridge_with_language_records_atoms():
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=3,
                                 enable_language_trace=True)
    bridge.process(C.Stimulus(payload="light", intensity=0.8, origin="world"))
    atoms = bridge.meaning_trace_builder.atoms
    assert len(atoms) >= 3
    predicates = {a.predicate for a in atoms}
    # received + encoded + substrate update + suggestion all present.
    assert {"received", "encoded_as", "updated", "suggested"} <= predicates


def test_snapshot_includes_last_explanation():
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=3,
                                 enable_language_trace=True)
    bridge.process(C.Stimulus(payload="x", intensity=0.6, origin="world"))
    snap = bridge.snapshot()
    lang = snap["language"]
    assert lang["enabled"] is True
    assert lang["meaning_atoms"] > 0
    assert "last_event" in lang["last_explanations"]
    assert "Stimulus" in lang["last_explanations"]["last_event"]["text"]


def test_language_disabled_by_default():
    bridge = SolarisNeuralBridge(action_labels=["a", "b"], seed=3)
    bridge.process(C.Stimulus(payload="x"))
    assert bridge.meaning_trace_builder is None
    assert "language" not in bridge.snapshot()
