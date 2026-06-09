"""Tests for the expanded event encoder."""

from __future__ import annotations

from solaris_ai_nn.signals import canonical as C
from solaris_ai_nn.signals.encoding import (
    KINDS,
    ORIGIN_BUCKETS,
    PAYLOAD_BUCKETS,
    SCALAR_FIELDS,
    EventEncoder,
)

_EXPECTED_SIZE = len(KINDS) + len(SCALAR_FIELDS) + 1 + PAYLOAD_BUCKETS + ORIGIN_BUCKETS


def test_vector_size_is_correct_and_consistent():
    enc = EventEncoder()
    assert enc.vector_size == _EXPECTED_SIZE
    assert enc.dim == enc.vector_size  # backwards-compatible alias
    s = C.Stimulus(payload="x", intensity=0.5)
    assert len(enc.encode(s)) == enc.vector_size


def test_encoding_is_deterministic():
    enc = EventEncoder()
    s = C.Stimulus(payload="food", intensity=0.5)
    assert enc.encode(s) == enc.encode(s)
    assert enc.encode(s, dt=0.3, heartbeat=True) == enc.encode(s, dt=0.3, heartbeat=True)


def test_different_types_differ_in_onehot_block():
    enc = EventEncoder()
    stim = enc.encode(C.Stimulus(payload="x"))
    push = enc.encode(C.Push(intensity=0.4))
    onehot = len(KINDS)
    # The signal-kind one-hot blocks differ between types.
    assert stim[:onehot] != push[:onehot]
    assert stim[KINDS.index("Stimulus")] == 1.0
    assert push[KINDS.index("Push")] == 1.0


def test_scalar_slots_carry_values():
    enc = EventEncoder()
    s = C.Stimulus(payload="x", intensity=0.9, is_absence=True)
    vec = enc.encode(s, dt=enc.max_dt)  # dt == max_dt => time_delta slot == 1.0
    base = len(KINDS)
    assert vec[base + SCALAR_FIELDS.index("intensity")] == 0.9
    assert vec[base + SCALAR_FIELDS.index("is_absence")] == 1.0
    assert vec[base + SCALAR_FIELDS.index("time_delta")] == 1.0


def test_logos_tension_includes_division_union_fracture():
    enc = EventEncoder()
    t = C.LogosTension(division=0.8, union=0.3)
    vec = enc.encode(t)
    base = len(KINDS)
    assert vec[base + SCALAR_FIELDS.index("division")] == 0.8
    assert vec[base + SCALAR_FIELDS.index("union")] == 0.3
    assert abs(vec[base + SCALAR_FIELDS.index("fracture")] - 0.5) < 1e-9


def test_vocabulary_gives_distinct_payload_slots():
    enc = EventEncoder(vocabulary=["light", "noise", "food"])
    keys = {enc.pattern_key(C.Stimulus(payload=p)) for p in ("light", "noise", "food")}
    assert len(keys) == 3  # no collisions among known vocabulary


def test_heartbeat_flag_slot():
    enc = EventEncoder()
    s = C.Stimulus(payload="x")
    hb_index = len(KINDS) + len(SCALAR_FIELDS)  # the single heartbeat slot
    assert enc.encode(s, heartbeat=True)[hb_index] == 1.0
    assert enc.encode(s, heartbeat=False)[hb_index] == 0.0
