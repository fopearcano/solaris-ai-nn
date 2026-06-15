"""FeederMonitor: active output detected; silent output; invalid counted."""

from __future__ import annotations

import os
import time

from solaris_ai_nn.feeder_sdk import (
    FeederMonitor,
    FeederSDKEnvelope,
    JSONLFeederWriter,
)


def _write(path, n=4):
    writer = JSONLFeederWriter(output_path=path, write_manifest=False)
    for i in range(n):
        writer.write(FeederSDKEnvelope(
            feeder_id="rf", source_id="rf", source_kind="k",
            modality="radio_frequency", features={"power": 0.6},
            timestamp=float(i)))


def test_active_output_detected(tmp_path):
    path = str(tmp_path / "rf.jsonl")
    _write(path)
    snap = FeederMonitor(silence_window_s=60.0).monitor([path])
    assert snap.active_count == 1
    assert snap.outputs[0].event_count == 4


def test_silent_output_detected(tmp_path):
    path = str(tmp_path / "echo.jsonl")
    _write(path, n=1)
    old = time.time() - 3600
    os.utime(path, (old, old))
    snap = FeederMonitor(silence_window_s=60.0).monitor([path])
    assert snap.silent_count == 1
    assert snap.outputs[0].silent is True


def test_invalid_event_counted(tmp_path):
    path = str(tmp_path / "bad.jsonl")
    with open(path, "w") as fh:
        fh.write('{"feeder_id":"x","source_id":"x","modality":"vibration",'
                 '"timestamp":1,"provenance":{"source_id":"x","feeder_id":"x"},'
                 '"features":{"amplitude":0.4}}\n')
        fh.write("{not valid json\n")
    snap = FeederMonitor().monitor([path])
    assert snap.invalid_event_count == 1


def test_missing_output_reported(tmp_path):
    snap = FeederMonitor().monitor([str(tmp_path / "missing.jsonl")])
    assert snap.outputs[0].exists is False
