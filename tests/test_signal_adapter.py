"""Tests for the robust, duck-typed SolarisSignalAdapter."""

from __future__ import annotations

from solaris_ai_nn.signals import canonical as C
from solaris_ai_nn.signals.adapters import (
    SolarisSignalAdapter,
    extract_payload,
    extract_signal_type,
    from_nn_action,
    from_nn_desire,
    to_nn_signal,
)


class FakeSolarisStimulus:
    """An object-like Solaris_Ai-style signal (not a canonical NN dataclass).

    Deliberately named so its class name is NOT in the canonical registry, so the
    adapter must fall back to field-based inference.
    """

    def __init__(self):
        self.id = 99
        self.timestamp = 123.0
        self.origin = "solaris"
        self.modality = "sensor"
        self.payload = "light"
        self.intensity = 0.8
        self.is_absence = False


class FakeSolarisLogos:
    def __init__(self):
        self.origin = "logos"
        self.division = 0.7
        self.union = 0.2


def test_dict_stimulus_to_canonical():
    adapter = SolarisSignalAdapter()
    raw = {"kind": "Stimulus", "modality": "sensor", "payload": "light", "intensity": 0.6}
    sig = adapter.to_nn_signal(raw)
    assert isinstance(sig, C.Stimulus)
    assert sig.payload == "light"
    assert sig.intensity == 0.6
    assert sig.modality == "sensor"


def test_object_like_signal_to_canonical_via_inference():
    sig = to_nn_signal(FakeSolarisStimulus())
    assert isinstance(sig, C.Stimulus)
    assert sig.payload == "light"
    assert sig.intensity == 0.8
    assert sig.origin == "solaris"


def test_object_like_logos_to_canonical():
    sig = to_nn_signal(FakeSolarisLogos())
    assert isinstance(sig, C.LogosTension)
    assert sig.division == 0.7
    assert sig.union == 0.2
    assert abs(sig.fracture - 0.5) < 1e-9


def test_native_signal_passes_through():
    original = C.Push(intensity=0.3, direction="reactive")
    assert to_nn_signal(original) is original


def test_handles_missing_optional_fields():
    # Only a kind + payload; everything else must fall back to defaults.
    sig = to_nn_signal({"kind": "Stimulus", "payload": "x"})
    assert isinstance(sig, C.Stimulus)
    assert sig.intensity == 0.0
    assert sig.is_absence is False
    assert sig.modality == "generic"


def test_preserves_is_absence():
    sig = to_nn_signal({"kind": "Stimulus", "payload": "I exist!", "is_absence": True})
    assert sig.is_absence is True


def test_extract_signal_type_variants():
    assert extract_signal_type({"kind": "Reaction", "valence": -1.0}) == "Reaction"
    # No explicit kind: inferred from fields.
    assert extract_signal_type({"action_id": 3, "valence": 0.5}) == "Reaction"
    assert extract_signal_type({"division": 0.1, "union": 0.9}) == "LogosTension"
    assert extract_signal_type({"payload": "x", "modality": "sensor"}) == "Stimulus"
    assert extract_signal_type(C.Action(name="approach")) == "Action"


def test_extract_payload_excludes_computed_and_markers():
    payload = extract_payload({"kind": "LogosTension", "division": 0.6, "union": 0.1, "fracture": 0.5})
    assert "kind" not in payload
    assert "fracture" not in payload
    assert payload["division"] == 0.6


def test_from_nn_action_and_desire():
    action = from_nn_action("approach", payload="ctx")
    assert isinstance(action, C.Action)
    assert action.name == "approach"
    assert action.payload == "ctx"

    desire = from_nn_desire("approach", motivation=0.4, confidence=0.8)
    assert isinstance(desire, C.Desire)
    assert desire.proposal == "approach"
    assert desire.confidence == 0.8
