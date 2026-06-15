"""LongHorizonDevelopmentalRuntime: bounded; persists; consumes outputs; no control."""

from __future__ import annotations

import inspect
import os

from solaris_ai_nn.developmental_life import LongHorizonDevelopmentalRuntime
from solaris_ai_nn.developmental_life import developmental_runtime


def _modules():
    return {
        "perceptual_metabolism": {"source_diet_diversity": 0.5},
        "perceptual_ontogenesis": {"proto_concept_count": 8,
                                   "stable_concept_count": 4},
        "sensorium_cognition": {"prediction_success_rate": 0.5}}


def test_runtime_bounded(tmp_path):
    dev = LongHorizonDevelopmentalRuntime(state_dir=str(tmp_path / "dev"),
                                          modules=_modules(), max_ticks=5)
    out = dev.run_bounded()
    assert out["refused"] is False
    assert dev.ticks_run <= 5


def test_persists_state(tmp_path):
    dev = LongHorizonDevelopmentalRuntime(state_dir=str(tmp_path / "dev"),
                                          modules=_modules(), max_ticks=4,
                                          epoch_tick_span=2)
    dev.run_bounded()
    assert os.path.isfile(tmp_path / "dev" / "developmental_index.json")
    # A fresh runtime reloads the persisted index (state survives restart).
    dev2 = LongHorizonDevelopmentalRuntime(state_dir=str(tmp_path / "dev"),
                                           modules=_modules(), max_ticks=1)
    assert dev2.memory.index.to_dict()["epoch_count"] >= 1


def test_consumes_previous_module_outputs(tmp_path):
    dev = LongHorizonDevelopmentalRuntime(state_dir=str(tmp_path / "dev"),
                                          modules=_modules(), max_ticks=2)
    dev.update(tick=0)
    statuses = dev._collect_statuses()
    assert "perceptual_ontogenesis" in statuses
    assert statuses["perceptual_ontogenesis"]["stable_concept_count"] == 4


def test_missing_modules_handled(tmp_path):
    dev = LongHorizonDevelopmentalRuntime(state_dir=str(tmp_path / "dev"),
                                          modules={}, max_ticks=2)
    out = dev.run_bounded()
    assert out["refused"] is False  # graceful with no modules attached


def test_unbounded_refused():
    dev = LongHorizonDevelopmentalRuntime(max_ticks=0, max_runtime_s=0)
    assert dev.update()["refused"] is True


def test_no_control_or_teaching_in_source():
    src = inspect.getsource(developmental_runtime)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "os.system" not in src
    assert "teaching_loop" not in src.lower()
