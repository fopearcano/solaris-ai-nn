"""Semiogenesis: sign history stored; latent replay rec; metabolism signals."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime


def _ontogenesis(tmp_path):
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
    return ont


def test_sign_history_stored(tmp_path):
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"),
                              ontogenesis=_ontogenesis(tmp_path), max_ticks=4)
    sem.run_bounded()
    assert os.path.isfile(tmp_path / "s" / "signs.jsonl")
    assert os.path.isfile(tmp_path / "s" / "sign_index.json")
    sid = next(iter(sem.signs))
    assert sem.memory.sign_history(sid)


def test_latent_replay_recommendation_created(tmp_path):
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"),
                              ontogenesis=_ontogenesis(tmp_path), max_ticks=4)
    sem.run_bounded()
    recs = sem.latent_replay_recommendations()
    assert isinstance(recs, list)
    assert 0 <= len(recs) <= 6  # bounded, never unbounded


def test_sign_overload_affects_metabolism(tmp_path):
    ont = _ontogenesis(tmp_path)
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"), ontogenesis=ont,
                              max_signs_per_tick=1, max_ticks=4)
    sem.run_bounded()
    signals = sem.metabolism_signals()
    # The metabolism-facing signals expose sign pressure (overload here).
    assert "sign_overload" in signals
    assert "sign_ambiguity_pressure" in signals
    assert signals["sign_overload"] is True  # capped birth raised warnings


def test_overloaded_metabolism_throttles_sign_birth(tmp_path):
    ont = _ontogenesis(tmp_path)
    overloaded = {"overload_state": True, "novelty_appetite_pressure": 0.0}
    calm = {"overload_state": False, "novelty_appetite_pressure": 0.0}
    over = SemiogenesisRuntime(state_dir=str(tmp_path / "ov"), ontogenesis=ont,
                               metabolism=overloaded, max_signs_per_tick=40,
                               max_ticks=1)
    out_over = over.update(tick=0)
    calm_rt = SemiogenesisRuntime(state_dir=str(tmp_path / "ca"),
                                  ontogenesis=ont, metabolism=calm,
                                  max_signs_per_tick=40, max_ticks=1)
    out_calm = calm_rt.update(tick=0)
    assert out_over["born_this_tick"] <= out_calm["born_this_tick"]
