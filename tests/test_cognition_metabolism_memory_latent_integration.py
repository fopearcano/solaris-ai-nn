"""Cognition: metabolism limits cognition; memory stores; latent replay rec."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.sensorium_cognition import SensoriumCognitionRuntime


def _stack(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in ("alien_rf", "alien_echo", "alien_vibration"):
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
    return sem, ont


def test_metabolism_limits_cognition(tmp_path):
    sem, ont = _stack(tmp_path)
    over = SensoriumCognitionRuntime(
        state_dir=str(tmp_path / "ov"), semiogenesis=sem, ontogenesis=ont,
        metabolism={"overload_state": True}, max_moves_per_tick=40,
        max_ticks=1)
    out_over = over.update(tick=0)
    calm = SensoriumCognitionRuntime(
        state_dir=str(tmp_path / "ca"), semiogenesis=sem, ontogenesis=ont,
        metabolism={"overload_state": False}, max_moves_per_tick=40,
        max_ticks=1)
    out_calm = calm.update(tick=0)
    # Overload throttles the move budget.
    assert out_over["move_count"] <= out_calm["move_count"]
    assert over.overload_events >= 1


def test_cognitive_memory_stores_traces(tmp_path):
    sem, ont = _stack(tmp_path)
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c"),
                                    semiogenesis=sem, ontogenesis=ont,
                                    max_ticks=2)
    cog.run_bounded()
    assert os.path.isfile(tmp_path / "c" / "cognitive_moves.jsonl")
    assert os.path.isfile(tmp_path / "c" / "predictions.jsonl")
    assert os.path.isfile(tmp_path / "c" / "cognitive_index.json")


def test_latent_replay_recommendation_exists(tmp_path):
    sem, ont = _stack(tmp_path)
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c"),
                                    semiogenesis=sem, ontogenesis=ont,
                                    max_ticks=1)
    cog.update(tick=0, observed_targets=["nonexistent"])
    recs = cog.latent_replay_recommendations()
    assert isinstance(recs, list)
    assert 0 <= len(recs) <= 6


def test_metabolism_signals_exposed(tmp_path):
    sem, ont = _stack(tmp_path)
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c"),
                                    semiogenesis=sem, ontogenesis=ont,
                                    max_ticks=2)
    cog.run_bounded()
    signals = cog.metabolism_signals()
    for key in ("cognitive_overload", "prediction_overload",
                "question_pressure_overload", "simulation_fatigue",
                "synthesis_pressure", "consolidation_pressure"):
        assert key in signals
