"""Developmental consumes Prompts 41-52 outputs; missing modules handled."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.developmental_life import LongHorizonDevelopmentalRuntime
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime


def _stack(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in ("alien_rf", "alien_vibration"):
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(12):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=3)
    ont = PerceptualOntogenesisRuntime(state_dir=str(tmp_path / "o"),
                                       sensorium=rt, max_ticks=6)
    ont.run_bounded()
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"), ontogenesis=ont,
                              max_ticks=5)
    sem.run_bounded()
    return rt, ont, sem


def test_consumes_real_module_outputs(tmp_path):
    rt, ont, sem = _stack(tmp_path)
    dev = LongHorizonDevelopmentalRuntime(
        state_dir=str(tmp_path / "dev"),
        modules={"plural_sensorium": rt, "perceptual_ontogenesis": ont,
                 "semiogenesis": sem}, max_ticks=4)
    dev.run_bounded()
    statuses = dev._collect_statuses()
    # Real runtime status methods were called.
    assert "perceptual_ontogenesis" in statuses
    assert "proto_concept_count" in statuses["perceptual_ontogenesis"]
    assert dev.growth.dimensions  # growth derived from real outputs


def test_missing_optional_modules_handled_gracefully(tmp_path):
    # Only a couple of modules attached; others missing -> no crash.
    dev = LongHorizonDevelopmentalRuntime(
        state_dir=str(tmp_path / "dev"),
        modules={"perceptual_metabolism": {"source_diet_diversity": 0.4}},
        max_ticks=3)
    out = dev.run_bounded()
    assert out["refused"] is False
    assert dev.developmental_status()["developmental_life_enabled"] is True


def test_object_without_status_method_handled(tmp_path):
    class _Bare:
        pass

    dev = LongHorizonDevelopmentalRuntime(
        state_dir=str(tmp_path / "dev"),
        modules={"perceptual_ontogenesis": _Bare()}, max_ticks=2)
    out = dev.run_bounded()
    assert out["refused"] is False
