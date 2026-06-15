"""SelfBoundaryRuntime: bounded; consumes sensorium/cognition; no control."""

from __future__ import annotations

import inspect
import json
import os

from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.self_boundary import SelfBoundaryRuntime
from solaris_ai_nn.self_boundary import self_boundary_runtime


def _sensorium(tmp_path, modalities=("alien_rf", "alien_vibration"), n=12):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in modalities:
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(n):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=3)
    return rt


def test_runtime_bounded(tmp_path):
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"),
                             sensorium=_sensorium(tmp_path), max_ticks=4)
    out = sb.run_bounded()
    assert out["refused"] is False
    assert sb.ticks_run <= 4


def test_consumes_sensorium_traces(tmp_path):
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"),
                             sensorium=_sensorium(tmp_path), max_ticks=2)
    sb.run_bounded()
    st = sb.self_boundary_status()
    assert st["receptor_body_schema_count"] > 0
    assert st["boundary_event_count"] > 0


def test_no_self_loop_explosion(tmp_path):
    sb = SelfBoundaryRuntime(state_dir=str(tmp_path / "sb"),
                             sensorium=_sensorium(tmp_path),
                             max_events_per_tick=1, max_ticks=2)
    sb.run_bounded()
    # The per-tick event cap bounds body-schema growth this tick.
    assert sb.body_schema.part_count <= 2


def test_unbounded_refused():
    sb = SelfBoundaryRuntime(max_ticks=0, max_runtime_s=0)
    assert sb.update()["refused"] is True


def test_no_hardware_source_or_action_in_source():
    src = inspect.getsource(self_boundary_runtime)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "os.system" not in src
