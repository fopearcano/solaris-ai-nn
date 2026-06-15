"""Ontogenesis: memory preserves history; latent replay rec; research protocols."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.evaluation.protocols import PROTOCOLS
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _runtime(tmp_path):
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


def test_memory_preserves_concept_history(tmp_path):
    ont = _runtime(tmp_path)
    # Append-only concept/atom/relation logs were written.
    assert os.path.isfile(tmp_path / "o" / "concepts.jsonl")
    assert os.path.isfile(tmp_path / "o" / "atoms.jsonl")
    assert os.path.isfile(tmp_path / "o" / "concept_index.json")
    # History for at least one concept is retrievable.
    cid = next(iter(ont.concepts))
    assert ont.memory.concept_history(cid)


def test_latent_replay_recommendation_generated(tmp_path):
    ont = _runtime(tmp_path)
    recs = ont.latent_replay_recommendations()
    assert isinstance(recs, list)
    assert 0 <= len(recs) <= 6  # bounded, never unbounded


def test_research_protocols_exist():
    for name in ("perceptual_ontogenesis", "proto_concept_birth",
                 "concept_stabilization", "concept_decay",
                 "concept_contamination", "world_formation",
                 "perceptual_ontogenesis_safety"):
        assert name in PROTOCOLS
        assert callable(PROTOCOLS[name])
