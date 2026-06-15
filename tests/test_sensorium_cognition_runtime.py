"""SensoriumCognitionRuntime: bounded; consumes signs/concepts; no control."""

from __future__ import annotations

import inspect
import json
import os

from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.sensorium_cognition import SensoriumCognitionRuntime
from solaris_ai_nn.sensorium_cognition import cognition_runtime


def _semiogenesis(tmp_path, modalities=("alien_rf", "alien_vibration"), n=12):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in modalities:
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(n):
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
    return sem, ont


def test_runtime_bounded(tmp_path):
    sem, ont = _semiogenesis(tmp_path)
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c"),
                                    semiogenesis=sem, ontogenesis=ont,
                                    max_ticks=4)
    out = cog.run_bounded()
    assert out["refused"] is False
    assert cog.ticks_run <= 4


def test_consumes_signs_concepts_metabolism(tmp_path):
    sem, ont = _semiogenesis(tmp_path)
    cog = SensoriumCognitionRuntime(
        state_dir=str(tmp_path / "c"), semiogenesis=sem, ontogenesis=ont,
        metabolism={"overload_state": False}, max_ticks=3)
    cog.run_bounded()
    st = cog.cognition_status()
    assert st["cognitive_move_count"] > 0
    assert st["prediction_count"] >= 0


def test_no_cognitive_explosion(tmp_path):
    sem, ont = _semiogenesis(tmp_path,
                             modalities=("alien_rf", "alien_echo",
                                         "alien_vibration", "thermal"))
    cog = SensoriumCognitionRuntime(
        state_dir=str(tmp_path / "c"), semiogenesis=sem, ontogenesis=ont,
        max_moves_per_tick=5, max_ticks=3)
    cog.run_bounded()
    # The per-tick move cap bounds the move set.
    assert len(cog.moves) <= 5


def test_unbounded_refused():
    cog = SensoriumCognitionRuntime(max_ticks=0, max_runtime_s=0)
    assert cog.update()["refused"] is True


def test_no_llm_hardware_source_or_action_in_source():
    src = inspect.getsource(cognition_runtime)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "os.system" not in src
    assert "openai" not in src.lower()
