"""Metabolism emits milestones, latent-replay recs, and auto-regen warnings."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_metabolism import PerceptualMetabolismRuntime
from solaris_ai_nn.perceptual_metabolism.metabolic_runtime import (
    MetabolismMilestone,
)
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _sensorium(tmp_path, modalities=("alien_rf", "alien_vibration"), n=10):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in modalities:
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(n):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=1)
    return rt


def test_developmental_milestones_emitted(tmp_path):
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"),
                                      sensorium=_sensorium(tmp_path))
    met.update(events_this_tick=16, tick=0)
    assert met.milestones  # at least the first need-pressure milestone
    assert all(m in MetabolismMilestone.ALL for m in met.milestones)


def test_overload_milestone_and_auto_regeneration_warning(tmp_path):
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"),
                                      sensorium=_sensorium(tmp_path),
                                      overload_threshold=10)
    met.update(events_this_tick=500, tick=0)
    assert MetabolismMilestone.FIRST_OVERLOAD in met.milestones
    # Overload may recommend auto-regeneration hygiene, never evidence deletion.
    auto = [r for r in met.recommendations if r["target"] == "auto_regeneration"]
    for rec in auto:
        assert "never delete raw evidence" in rec["note"]


def test_deprivation_milestone_treats_silence_as_stimulus(tmp_path):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "empty"))
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"), sensorium=rt)
    met.update(events_this_tick=0, tick=0)
    assert MetabolismMilestone.FIRST_DEPRIVATION in met.milestones
    assert MetabolismMilestone.FIRST_SILENCE_AS_STIMULUS in met.milestones


def test_latent_replay_recommendations_bounded(tmp_path):
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "s"),
                                      sensorium=_sensorium(tmp_path))
    met.update(events_this_tick=12, tick=0)
    recs = met.latent_replay_recommendations()
    assert isinstance(recs, list)
    assert 0 <= len(recs) <= 6  # bounded recommendation list, never unbounded


def test_no_sensorium_yields_no_replay_recs():
    met = PerceptualMetabolismRuntime(max_ticks=5)
    assert met.latent_replay_recommendations() == []
