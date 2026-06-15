"""Cognition: world model receives prediction; hypothesis failed pred; LOGOS."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime
from solaris_ai_nn.sensorium_cognition import SensoriumCognitionRuntime


def _runtime(tmp_path, observed=None):
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
    cog = SensoriumCognitionRuntime(state_dir=str(tmp_path / "c"),
                                    semiogenesis=sem, ontogenesis=ont,
                                    max_ticks=1)
    # Force at least one failed prediction by observing nothing.
    cog.update(tick=0, observed_targets=observed if observed is not None
               else ["nonexistent_target"])
    return cog


def test_world_model_receives_prediction(tmp_path):
    cog = _runtime(tmp_path)
    nodes = cog.world_model_nodes()
    assert nodes
    pred_nodes = [n for n in nodes if n["attributes"]["role"] == "prediction"]
    sim_nodes = [n for n in nodes if n["attributes"]["role"] == "simulation"]
    assert pred_nodes
    # Simulation nodes are marked non-real and never mixed with observation.
    for n in sim_nodes:
        assert n["attributes"]["simulated"] is True
        assert n["attributes"]["is_real_observation"] is False


def test_hypothesis_receives_failed_prediction(tmp_path):
    cog = _runtime(tmp_path)
    assert cog.failed_predictions  # observing nothing -> failures
    seeds = cog.hypothesis_seeds()
    assert any(s.hypothesis_type == "anomaly" for s in seeds)
    assert all(s.source == "sensorium_cognition" for s in seeds)


def test_logos_receives_tension(tmp_path):
    cog = _runtime(tmp_path)
    tensions = cog.logos_tensions()
    assert tensions
    from solaris_ai_nn.logos_complexity.tension import TensionType
    assert all(t.tension_type in TensionType.ALL for t in tensions)
    assert any("cognition_tension" in t.metadata for t in tensions)
