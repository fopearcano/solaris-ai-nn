"""Tests for canonical signals, the event encoder, and adapters."""

from __future__ import annotations

from solaris_ai_nn.signals import canonical as C
from solaris_ai_nn.signals.adapters import dict_to_signal, signal_to_dict
from solaris_ai_nn.signals.encoding import KINDS, PAYLOAD_BUCKETS, EventEncoder


def test_signal_creation_fields():
    s = C.Stimulus(modality="sensor", payload="light", intensity=0.7)
    assert s.kind == "Stimulus"
    assert s.intensity == 0.7
    assert s.is_absence is False
    assert isinstance(s.id, int) and s.id > 0
    assert s.timestamp > 0


def test_unique_monotonic_ids():
    a = C.Push()
    b = C.Push()
    assert b.id > a.id


def test_logos_tension_fracture():
    t = C.LogosTension(division=0.8, union=0.3)
    assert abs(t.fracture - 0.5) < 1e-9
    # fracture is symmetric and non-negative
    assert C.LogosTension(division=0.3, union=0.8).fracture == t.fracture


def test_reaction_valence_range_is_caller_responsibility():
    r = C.Reaction(action_id=1, valence=-1.0)
    assert r.valence == -1.0


def test_encoder_dimension_is_fixed():
    enc = EventEncoder()
    assert enc.dim == len(KINDS) + 4 + PAYLOAD_BUCKETS + 2


def test_encode_stimulus_onehot_and_scalars():
    enc = EventEncoder()
    s = C.Stimulus(modality="sensor", payload="light", intensity=0.9)
    vec = enc.encode(s, dt=0.5, heartbeat=True)
    assert len(vec) == enc.dim
    # Stimulus one-hot slot is set.
    assert vec[KINDS.index("Stimulus")] == 1.0
    # intensity scalar slot is right after the one-hot block.
    assert vec[len(KINDS)] == 0.9
    # heartbeat flag (second-to-last slot) is set.
    assert vec[-2] == 1.0


def test_encode_is_deterministic():
    enc = EventEncoder()
    s = C.Stimulus(payload="food", intensity=0.5)
    assert enc.encode(s) == enc.encode(s)


def test_pattern_key_groups_by_kind_and_payload():
    enc = EventEncoder()
    a = C.Stimulus(payload="light")
    b = C.Stimulus(payload="light")
    c = C.Stimulus(payload="noise")
    assert enc.pattern_key(a) == enc.pattern_key(b)
    # Different payloads may or may not collide in 8 buckets, but key format holds.
    assert enc.pattern_key(c).startswith("Stimulus:")


def test_adapter_roundtrip():
    s = C.Stimulus(modality="sensor", payload="light", intensity=0.4, is_absence=True)
    data = signal_to_dict(s)
    assert data["kind"] == "Stimulus"
    back = dict_to_signal(data)
    assert isinstance(back, C.Stimulus)
    assert back.payload == "light"
    assert back.is_absence is True
    assert back.intensity == 0.4


def test_adapter_exposes_computed_fracture():
    t = C.LogosTension(division=0.6, union=0.1)
    data = signal_to_dict(t)
    assert "fracture" in data
    assert abs(data["fracture"] - 0.5) < 1e-9
    # Rebuild ignores the computed field gracefully.
    back = dict_to_signal(data)
    assert isinstance(back, C.LogosTension)
    assert abs(back.fracture - 0.5) < 1e-9
