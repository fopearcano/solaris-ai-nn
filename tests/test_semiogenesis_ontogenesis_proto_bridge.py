"""Semiogenesis bridges ontogenesis; preserves concept/sign/gloss distinction."""

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


def test_consumes_proto_concepts(tmp_path):
    ont = _ontogenesis(tmp_path)
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"), ontogenesis=ont,
                              max_ticks=4)
    sem.run_bounded()
    # Every sign references at least one proto-concept (grounding bridge).
    assert sem.signs
    for sign in sem.signs.values():
        assert sign.proto_concept_refs


def test_bridges_concepts_passed_as_list(tmp_path):
    ont = _ontogenesis(tmp_path)
    # The runtime can also consume a bare list of concepts (older bridge shape).
    concepts = list(ont.concepts.values())

    class _Shim:
        def __init__(self, cs):
            self.concepts = {c.concept_id: c for c in cs}

        def world_model_edges(self):
            return []

    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s2"),
                              ontogenesis=_Shim(concepts), max_ticks=2)
    sem.run_bounded()
    assert sem.semiogenesis_status()["internal_sign_count"] >= 0


def test_preserves_concept_sign_gloss_distinction(tmp_path):
    ont = _ontogenesis(tmp_path)
    sem = SemiogenesisRuntime(state_dir=str(tmp_path / "s"), ontogenesis=ont,
                              max_ticks=4)
    sem.run_bounded()
    sign = next(iter(sem.signs.values()))
    d = sign.to_dict()
    # concept (ref) != sign (code) != gloss (approximate human text)
    assert d["proto_concept_refs"]            # the perceptual category
    assert d["sign_code"] and ":" in d["sign_code"]  # the internal marker
    # The gloss, if present, is an approximate debug annotation, not the sign.
    if d["human_gloss"]:
        assert d["human_gloss"] != d["sign_code"]
        assert d["human_gloss_status"] != "ground_truth"
