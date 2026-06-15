#!/usr/bin/env python3
"""Perceptual ontogenesis demo: sensorium traces -> atoms -> proto-concepts.

    python examples/run_perceptual_ontogenesis_demo.py --state-dir .solaris_ai_nn_ontogenesis/test_ontogenesis

Feeds a mixed fixture sensorium into the perceptual-ontogenesis runtime, which
extracts perceptual atoms, conservatively proposes proto-concepts, stabilizes/
decays them, forms families and relations, and writes the report. Proto-concepts
are operational internal structures, NOT words or human categories.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.perceptual_metabolism import PerceptualMetabolismRuntime
from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _feeder(base, mod, fn, n=12):
    path = os.path.join(base, f"{fn}.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": mod, "v": 0.6 + 0.3 * (i % 2),
                                 "ts": float(i)}) + "\n")
    return fixture_feeder(f"{fn}_feed", path, mod)


def main():
    parser = argparse.ArgumentParser(description="Perceptual ontogenesis demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_ontogenesis/test_ontogenesis")
    args = parser.parse_args()
    base = args.state_dir
    feeds = os.path.join(base, "feeds")
    os.makedirs(feeds, exist_ok=True)

    sensorium = PluralSensoriumRuntime(state_dir=base)
    sensorium.add_feeder(_feeder(feeds, "alien_rf", "rf"))
    sensorium.add_feeder(_feeder(feeds, "alien_vibration", "vib"))
    sensorium.run_bounded(max_polls=3)

    met = PerceptualMetabolismRuntime(state_dir=base, sensorium=sensorium)
    met.update(events_this_tick=16, tick=0)

    ont = PerceptualOntogenesisRuntime(state_dir=base, sensorium=sensorium,
                                       metabolism=met, max_ticks=6)
    ont.run_bounded()
    status = ont.ontogenesis_status()
    out = ont.write_artifacts()

    print("=== Perceptual ontogenesis demo ===")
    print(f"active modalities     : {sensorium.active_modalities()}")
    print(f"perceptual atoms      : {status['perceptual_atom_count']}")
    print(f"proto-concepts        : {status['proto_concept_count']} "
          f"(stable {status['stable_concept_count']})")
    print(f"concept families      : {status['concept_family_count']} "
          f"(dominant {status['dominant_concept_family']})")
    print(f"concept relations     : {status['concept_relation_count']}")
    print(f"modality-native ratio : {status['modality_native_concept_ratio']}")
    print(f"contamination score   : {status['human_label_contamination_score']}")
    print(f"world formation density: {status['world_formation_density']}")
    print(f"report                : {out['markdown']}")
    print("note                  : proto-concepts are operational structures "
          "for compression, prediction, attention, and relation-building; they "
          "are not words and do not prove understanding or subjective "
          "experience.")


if __name__ == "__main__":
    main()
