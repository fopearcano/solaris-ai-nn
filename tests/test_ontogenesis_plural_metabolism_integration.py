"""Ontogenesis consumes Plural Sensorium traces and Perceptual Metabolism state."""

from __future__ import annotations

import json
import os

from solaris_ai_nn.perceptual_metabolism import PerceptualMetabolismRuntime
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _sensorium(tmp_path, modalities=("alien_rf", "alien_vibration"), n=12):
    rt = PluralSensoriumRuntime(state_dir=str(tmp_path / "ps"))
    for mod in modalities:
        path = os.path.join(str(tmp_path), f"{mod}.jsonl")
        with open(path, "w") as fh:
            for i in range(n):
                fh.write(json.dumps({"modality": mod, "v": 0.6,
                                     "ts": float(i)}) + "\n")
        rt.add_feeder(fixture_feeder(f"{mod}_feed", path, mod))
    rt.run_bounded(max_polls=3)
    return rt


def test_consumes_plural_sensorium_traces(tmp_path):
    rt = _sensorium(tmp_path)
    ont = PerceptualOntogenesisRuntime(state_dir=str(tmp_path / "o"),
                                       sensorium=rt, max_ticks=6)
    ont.run_bounded()
    # Atoms were extracted from sensorium invariants/rhythms/etc.
    assert ont.ontogenesis_status()["perceptual_atom_count"] > 0
    assert ont.ontogenesis_status()["proto_concept_count"] > 0


def test_consumes_perceptual_metabolism_state(tmp_path):
    rt = _sensorium(tmp_path)
    met = PerceptualMetabolismRuntime(state_dir=str(tmp_path / "m"),
                                      sensorium=rt)
    met.update(events_this_tick=16, tick=0)
    ont = PerceptualOntogenesisRuntime(state_dir=str(tmp_path / "o"),
                                       sensorium=rt, metabolism=met,
                                       max_ticks=3)
    ont.update(tick=0)
    # The metabolism status is readable and feeds birth modulation.
    assert ont._metabolism_status()  # non-empty dict


def test_overload_affects_concept_birth_priority(tmp_path):
    rt = _sensorium(tmp_path)
    # A metabolism state reporting overload throttles per-tick concept birth.
    overloaded = {"overload_state": True, "deprivation_state": False,
                  "novelty_appetite_pressure": 0.0}
    calm = {"overload_state": False, "deprivation_state": False,
            "novelty_appetite_pressure": 0.0}

    ont_over = PerceptualOntogenesisRuntime(
        state_dir=str(tmp_path / "over"), sensorium=rt, metabolism=overloaded,
        max_concepts_per_tick=40, max_ticks=1)
    out_over = ont_over.update(tick=0)
    ont_calm = PerceptualOntogenesisRuntime(
        state_dir=str(tmp_path / "calm"), sensorium=rt, metabolism=calm,
        max_concepts_per_tick=40, max_ticks=1)
    out_calm = ont_calm.update(tick=0)
    # Overload births no more concepts than the calm run on the first tick.
    assert out_over["born_this_tick"] <= out_calm["born_this_tick"]
