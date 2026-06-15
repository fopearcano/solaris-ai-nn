"""PerceptualMetabolismRuntime: bounded; consumes sensorium; no external control."""

from __future__ import annotations

import inspect
import json
import os

from solaris_ai_nn.perceptual_metabolism import PerceptualMetabolismRuntime
from solaris_ai_nn.perceptual_metabolism import metabolic_runtime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _sensorium(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod, fn in (("alien_rf", "rf"), ("alien_vibration", "vib")):
        path = os.path.join(str(tmp_path), f"{fn}.jsonl")
        with open(path, "w") as fh:
            for i in range(8):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{fn}_feed", path, mod))
    rt.run_bounded(max_polls=1)
    return rt


def test_runtime_bounded(tmp_path):
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"),
                                      sensorium=_sensorium(tmp_path),
                                      max_ticks=5)
    out = met.run_bounded()
    assert out["refused"] is False
    assert met.ticks_run <= 5


def test_consumes_sensorium_state(tmp_path):
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"),
                                      sensorium=_sensorium(tmp_path))
    met.update(events_this_tick=16, tick=0)
    status = met.metabolism_status()
    assert status["perceptual_need_count"] > 0
    assert status["source_diet_diversity"] >= 0.0


def test_produces_recommendations(tmp_path):
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"),
                                      sensorium=_sensorium(tmp_path),
                                      overload_threshold=10)
    met.update(events_this_tick=200, tick=0)
    assert met.recommendations  # overload/homeostasis recommendations present


def test_no_external_control_in_source():
    src = inspect.getsource(metabolic_runtime)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "os.system" not in src


def test_unbounded_refused():
    met = PerceptualMetabolismRuntime(max_ticks=0, max_runtime_s=0)
    out = met.update()
    assert out["refused"] is True
