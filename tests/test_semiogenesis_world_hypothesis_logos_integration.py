"""Semiogenesis: world sign node, hypothesis sign reference, LOGOS tension."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.semiogenesis import SemiogenesisRuntime


def _runtime(tmp_path, modalities=("alien_rf", "alien_echo", "alien_vibration")):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in modalities:
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
    return sem


def test_world_sign_node_created(tmp_path):
    sem = _runtime(tmp_path)
    nodes = sem.world_model_nodes()
    assert nodes
    # Signs are proto-symbol reference nodes, marked as role=sign (not concepts).
    assert all(n["type"] == "proto_symbol" for n in nodes)
    assert all(n["attributes"]["role"] == "sign" for n in nodes)
    assert all("not a human word" in n["attributes"]["note"] for n in nodes)


def test_hypothesis_uses_sign_reference(tmp_path):
    sem = _runtime(tmp_path)
    seeds = sem.hypothesis_seeds()
    assert seeds
    assert all(s.source == "semiogenesis" for s in seeds)


def test_logos_tension_created(tmp_path):
    sem = _runtime(tmp_path)
    tensions = sem.logos_tensions()
    assert tensions
    from solaris_ai_nn.logos_complexity.tension import TensionType
    assert all(t.tension_type in TensionType.ALL for t in tensions)
    assert any("semiogenesis_tension" in t.metadata for t in tensions)
