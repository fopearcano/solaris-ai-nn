"""Tests for the SignalMirror."""

from __future__ import annotations

import json

from solaris_ai_nn.experiments.solaris_sidecar_observation import Stimulus
from solaris_ai_nn.integration.signal_mirror import SignalMirror
from solaris_ai_nn.signals import canonical as C


def _mirror_one(mirror: SignalMirror, payload="light", vector=None):
    raw = Stimulus(payload=payload, intensity=0.6)
    adapted = C.Stimulus(payload=payload, intensity=0.6, origin="fake")
    return mirror.mirror(raw, adapted, vector)


def test_mirrors_raw_and_adapted():
    mirror = SignalMirror()
    record = _mirror_one(mirror, vector=[3.0, 4.0])
    assert record is not None
    assert record.raw_type == "Stimulus"
    assert record.adapted_kind == "Stimulus"
    assert record.raw_id is not None
    assert record.vector_len == 2
    assert abs(record.vector_norm - 5.0) < 1e-9
    assert record.vector is None  # summaries only by default


def test_full_payloads_mode_keeps_vector():
    mirror = SignalMirror(full_payloads=True)
    record = _mirror_one(mirror, vector=[1.0, 0.0])
    assert record.vector == [1.0, 0.0]


def test_does_not_mutate_original_signal():
    mirror = SignalMirror()
    raw = Stimulus(payload="light", intensity=0.6)
    before = dict(raw.__dict__)
    mirror.mirror(raw, C.Stimulus(payload="light"), [1.0])
    assert raw.__dict__ == before


def test_count_by_type_and_tail():
    mirror = SignalMirror()
    _mirror_one(mirror, "light")
    _mirror_one(mirror, "noise")
    mirror.mirror(object(), C.Reaction(valence=1.0))
    counts = mirror.count_by_type()
    assert counts["Stimulus"] == 2
    assert counts["Reaction"] == 1
    tail = mirror.tail(2)
    assert len(tail) == 2
    assert tail[-1]["adapted_kind"] == "Reaction"


def test_type_filter_skips():
    mirror = SignalMirror(allowed_types=["Reaction"])
    assert _mirror_one(mirror) is None
    assert mirror.skipped == 1
    assert len(mirror) == 0


def test_bounded_capacity():
    mirror = SignalMirror(capacity=3)
    for i in range(10):
        _mirror_one(mirror, f"p{i}")
    assert len(mirror) == 3


def test_jsonl_export(tmp_path):
    mirror = SignalMirror()
    _mirror_one(mirror, "light", vector=[1.0])
    _mirror_one(mirror, "noise", vector=[2.0])
    path = tmp_path / "mirrored_signals.jsonl"
    count = mirror.to_jsonl(path)
    assert count == 2
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert len(rows) == 2
    assert rows[0]["adapted_kind"] == "Stimulus"
    assert "vector_norm" in rows[0]


def test_snapshot():
    mirror = SignalMirror()
    _mirror_one(mirror)
    snap = mirror.snapshot()
    assert snap["mirrored"] == 1
    assert snap["by_type"] == {"Stimulus": 1}
    assert snap["full_payloads"] is False
