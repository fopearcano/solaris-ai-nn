"""OverloadDetector: event flood + proto-symbol explosion; evidence not deleted."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_metabolism import OverloadDetector
from solaris_ai_nn.perceptual_metabolism.overload import OverloadKind
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _sensorium(tmp_path, n=8):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    path = os.path.join(str(tmp_path), "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.7,
                                 "ts": float(i)}) + "\n")
    rt.add_feeder(fixture_feeder("rf_feed", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    return rt


def test_event_flood_detected(tmp_path):
    rt = _sensorium(tmp_path)
    det = OverloadDetector(events_per_tick_threshold=20)
    events = det.detect(events_this_tick=200, sensorium=rt)
    assert any(e.kind == OverloadKind.EVENT_FLOOD for e in events)
    assert det.state.overloaded


def test_proto_symbol_explosion_detected(tmp_path):
    rt = _sensorium(tmp_path)
    # Force a large proto-symbol pile.
    rt.proto_symbol_candidates = [{"symbol_type": "rf_grounded_symbol"}] * 50
    det = OverloadDetector(explosion_threshold=40)
    events = det.detect(events_this_tick=0, sensorium=rt)
    assert any(e.kind == OverloadKind.PROTO_SYMBOL_EXPLOSION for e in events)


def test_evidence_not_deleted(tmp_path):
    rt = _sensorium(tmp_path)
    before = sum(r.event_count for r in rt.receptors.values())
    OverloadDetector().detect(events_this_tick=500, sensorium=rt)
    after = sum(r.event_count for r in rt.receptors.values())
    assert after == before  # the detector deletes nothing
    assert "no evidence is deleted" in \
        OverloadDetector().state.to_dict()["note"]
