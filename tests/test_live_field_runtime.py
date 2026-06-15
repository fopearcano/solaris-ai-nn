"""LiveFieldRuntime: bounded; events reach sensorium; no mutation/auto-start."""

from __future__ import annotations

import inspect
import json
import os

from solaris_ai_nn.live_field import (
    LiveFeederDescriptor,
    LiveFeederMode,
    LiveFeederRegistry,
    LiveFieldRuntime,
)
from solaris_ai_nn.live_field import live_field_runtime


def _runtime(tmp_path, **kw):
    base = str(tmp_path / "live")
    os.makedirs(base, exist_ok=True)
    reg = LiveFeederRegistry(live_root=base)
    rf = os.path.join(base, "rf.jsonl")
    with open(rf, "w") as fh:
        for i in range(8):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    reg.register(LiveFeederDescriptor(
        feeder_id="rf_feed", source_id="rf", modality="alien_rf",
        mode=LiveFeederMode.LOCAL_FILE, output_path=rf))
    return LiveFieldRuntime(state_dir=base, live_root=base, registry=reg, **kw), rf


def test_runtime_bounded(tmp_path):
    rt, _ = _runtime(tmp_path, max_events_total=5)
    rt.run(live=False)
    assert rt.sensorium.events_ingested <= 5


def test_events_passed_to_plural_sensorium(tmp_path):
    rt, _ = _runtime(tmp_path)
    rt.run(live=False)
    assert rt.sensorium.receptors
    assert rt.sensorium.events_ingested > 0


def test_no_source_mutation(tmp_path):
    rt, rf = _runtime(tmp_path)
    before = open(rf).read()
    rt.run(live=False)
    assert open(rf).read() == before


def test_no_feeder_autostart_in_source():
    src = inspect.getsource(live_field_runtime)
    assert "subprocess" not in src
    assert "os.system" not in src
    assert "import socket" not in src


def test_live_mode_requires_governance(tmp_path):
    rt, _ = _runtime(tmp_path, governance=None)
    out = rt.run(live=True)
    assert out["refused"] is True
    assert any("governance" in r for r in out["reasons"])
