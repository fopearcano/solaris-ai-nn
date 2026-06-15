"""Live field <-> Plural sensorium: receptor + field updated; absence detected."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.live_field import (
    LiveFeederDescriptor,
    LiveFeederMode,
    LiveFeederRegistry,
    LiveFieldRuntime,
)
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime


def _runtime(tmp_path):
    base = str(tmp_path / "live")
    os.makedirs(base, exist_ok=True)
    reg = LiveFeederRegistry(live_root=base)
    rf = os.path.join(base, "rf.jsonl")
    with open(rf, "w") as fh:
        for i in range(10):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.7,
                                 "ts": float(i)}) + "\n")
    reg.register(LiveFeederDescriptor(
        feeder_id="rf_feed", source_id="rf", modality="alien_rf",
        mode=LiveFeederMode.LOCAL_FILE, output_path=rf,
        expected_silence_window_s=2.0))
    return LiveFieldRuntime(state_dir=base, live_root=base, registry=reg,
                            max_ticks=30)


def test_receptor_updated_from_live_envelope(tmp_path):
    rt = _runtime(tmp_path)
    rt.run(live=False)
    assert isinstance(rt.sensorium, PluralSensoriumRuntime)
    assert rt.sensorium.receptors
    assert any(r.event_count > 0 for r in rt.sensorium.receptors.values())


def test_sensory_field_updated(tmp_path):
    rt = _runtime(tmp_path)
    rt.run(live=False)
    assert rt.sensorium.sensory_field.tick > 1


def test_absence_detected_from_source_health(tmp_path):
    rt = _runtime(tmp_path)
    rt.run(live=False)
    # After the feeder's events end, the source health monitor records silence.
    rt.health.check_silence(now=1000.0)
    assert rt.health.silent_sources()
