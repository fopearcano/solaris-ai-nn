"""SemiogenesisRuntime: bounded; consumes concepts; sign cap; no LLM/control."""

from __future__ import annotations

import inspect
import json
import os

from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.semiogenesis import semiogenesis_runtime


def _ontogenesis(tmp_path, modalities=("alien_rf", "alien_vibration"), n=12):
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
    return ont


def test_runtime_bounded(tmp_path):
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"),
                              ontogenesis=_ontogenesis(tmp_path), max_ticks=5)
    out = sem.run_bounded()
    assert out["refused"] is False
    assert sem.ticks_run <= 5


def test_consumes_ontogenesis_concepts(tmp_path):
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"),
                              ontogenesis=_ontogenesis(tmp_path), max_ticks=5)
    sem.run_bounded()
    assert sem.semiogenesis_status()["internal_sign_count"] > 0


def test_sign_cap_prevents_explosion(tmp_path):
    ont = _ontogenesis(tmp_path, modalities=("alien_rf", "alien_echo",
                                             "alien_vibration", "thermal"))
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"), ontogenesis=ont,
                              max_signs_per_tick=2, max_ticks=4)
    sem.run_bounded()
    assert sem.explosion_warnings >= 1


def test_unbounded_refused():
    sem = SemiogenesisRuntime(max_ticks=0, max_runtime_s=0)
    assert sem.update()["refused"] is True


def test_no_llm_hardware_or_action_control_in_source():
    src = inspect.getsource(semiogenesis_runtime)
    assert "subprocess" not in src
    assert "import socket" not in src
    assert "os.system" not in src
    # No LLM / language-model client is imported or called.
    assert "openai" not in src.lower()
    assert "language_model" not in src.lower()
