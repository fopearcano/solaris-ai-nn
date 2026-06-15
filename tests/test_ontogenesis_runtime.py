"""PerceptualOntogenesisRuntime: bounded; consumes state; capped; no control."""

from __future__ import annotations

import inspect
import json
import os

from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.perceptual_ontogenesis import ontogenesis_runtime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


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
    ont = PerceptualOntogenesisRuntime(state_dir=str(tmp_path / "o"),
                                       sensorium=_sensorium(tmp_path),
                                       max_ticks=5)
    out = ont.run_bounded()
    assert out["refused"] is False
    assert ont.ticks_run <= 5


def test_consumes_sensorium_state(tmp_path):
    ont = PerceptualOntogenesisRuntime(state_dir=str(tmp_path / "o"),
                                       sensorium=_sensorium(tmp_path),
                                       max_ticks=6)
    ont.run_bounded()
    st = ont.ontogenesis_status()
    assert st["perceptual_atom_count"] > 0
    assert st["proto_concept_count"] > 0


def test_concept_cap_prevents_explosion(tmp_path):
    ont = PerceptualOntogenesisRuntime(
        state_dir=str(tmp_path / "o"),
        sensorium=_sensorium(tmp_path,
                             modalities=("alien_rf", "alien_echo",
                                         "alien_vibration", "thermal")),
        max_concepts_per_tick=2, max_ticks=4)
    ont.run_bounded()
    # The per-tick cap bounds growth and raises explosion warnings.
    assert ont.explosion_warnings >= 1


def test_unbounded_refused():
    ont = PerceptualOntogenesisRuntime(max_ticks=0, max_runtime_s=0)
    assert ont.update()["refused"] is True


def test_no_hardware_source_or_action_control_in_source():
    src = inspect.getsource(ontogenesis_runtime)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "os.system" not in src
