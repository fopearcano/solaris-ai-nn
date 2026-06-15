"""Ontogenesis: proto-language sign optional, world-model node, hypothesis, LOGOS."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


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
    return ont


def test_proto_language_sign_optional(tmp_path):
    ont = _runtime(tmp_path)
    signs = ont.proto_language_signs()
    # Signs are internal shorthand, not human words; not every concept gets one.
    assert isinstance(signs, list)
    assert len(signs) <= ont.ontogenesis_status()["proto_concept_count"]
    for s in signs:
        assert "not a human word" in s["note"]
        assert s["sign_kind"] in ("modality_native", "cross_modal",
                                  "human_label_contaminated")


def test_world_model_node_created(tmp_path):
    ont = _runtime(tmp_path)
    nodes = ont.world_model_nodes()
    assert nodes
    # Modality-native ontology preserved: proto-symbol/boundary, not human objects.
    assert all(n["type"] in ("proto_symbol", "boundary") for n in nodes)
    assert all("not a human object" in n["attributes"]["note"] for n in nodes)


def test_hypothesis_seeded_from_concept(tmp_path):
    ont = _runtime(tmp_path)
    seeds = ont.hypothesis_seeds()
    assert seeds
    assert all(s.source == "perceptual_ontogenesis" for s in seeds)
    assert all(s.evidence_refs is not None for s in seeds)


def test_logos_tension_created(tmp_path):
    ont = _runtime(tmp_path)
    tensions = ont.logos_tensions()
    assert tensions
    # Tensions carry the ontogenesis semantic in metadata and use valid types.
    from solaris_ai_nn.logos_complexity.tension import TensionType
    assert all(t.tension_type in TensionType.ALL for t in tensions)
    assert any("ontogenesis_tension" in t.metadata for t in tensions)
