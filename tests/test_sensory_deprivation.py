"""DeprivationDetector: source silence detected; absence rises; silence stimulus."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_metabolism import DeprivationDetector
from solaris_ai_nn.perceptual_metabolism.deprivation import (
    DeprivationKind,
    DeprivationResponse,
)
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def test_empty_field_is_starvation(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    det = DeprivationDetector()
    events = det.detect(sensorium=rt)
    assert any(e.kind == DeprivationKind.SENSORY_STARVATION for e in events)
    assert det.state.deprived


def test_source_silence_detected(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    path = os.path.join(str(tmp_path), "rf.jsonl")
    with open(path, "w") as fh:
        for i in range(4):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    rt.add_feeder(fixture_feeder("rf_feed", path, "alien_rf"))
    rt.run_bounded(max_polls=1)
    for r in rt.receptors.values():
        r.silence_duration = 5.0
    det = DeprivationDetector()
    events = det.detect(sensorium=rt)
    assert any(e.kind == DeprivationKind.MODALITY_ABSENT_TOO_LONG
               for e in events)


def test_silence_becomes_stimulus_like_signal(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    det = DeprivationDetector()
    events = det.detect(sensorium=rt)
    responses = {r for e in events for r in e.responses}
    assert DeprivationResponse.PRESERVE_SILENCE_AS_STIMULUS in responses
    assert "silence is stimulus" in det.state.to_dict()["note"]
