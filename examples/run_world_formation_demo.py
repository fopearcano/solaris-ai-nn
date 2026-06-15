#!/usr/bin/env python3
"""World formation demo: concept families, relations, and world summary.

    python examples/run_world_formation_demo.py --state-dir .solaris_ai_nn_ontogenesis/test_world_formation

Runs ontogenesis over a multi-modal fixture sensorium and shows the concept
families, the relation graph, and the observable structural world summary. The
world formed here is a structural world, NOT subjective experience or qualia.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.perceptual_ontogenesis import PerceptualOntogenesisRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _feeder(base, mod, fn, n=12):
    path = os.path.join(base, f"{fn}.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": mod, "v": 0.5 + 0.4 * (i % 2),
                                 "ts": float(i)}) + "\n")
    return fixture_feeder(f"{fn}_feed", path, mod)


def main():
    parser = argparse.ArgumentParser(description="World formation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_ontogenesis/test_world_formation")
    args = parser.parse_args()
    base = args.state_dir
    feeds = os.path.join(base, "feeds")
    os.makedirs(feeds, exist_ok=True)

    sensorium = PluralSensoriumRuntime(state_dir=base)
    for mod, fn in (("alien_rf", "rf"), ("alien_echo", "echo"),
                    ("alien_vibration", "vib"), ("thermal", "therm")):
        sensorium.add_feeder(_feeder(feeds, mod, fn))
    sensorium.run_bounded(max_polls=3)

    ont = PerceptualOntogenesisRuntime(state_dir=base, sensorium=sensorium,
                                       max_ticks=6)
    ont.run_bounded()
    status = ont.ontogenesis_status()
    world = ont.world.to_dict()
    out = ont.write_artifacts()

    print("=== World formation demo ===")
    print(f"concept families      : {ont.family_builder.distribution()}")
    print(f"dominant family       : {status['dominant_concept_family']}")
    print(f"concept relations     : {status['concept_relation_count']}")
    print(f"relation graph density: "
          f"{world['state']['relation_graph_density']}")
    print(f"cross-modal integ.    : {world['state']['cross_modal_integration']}")
    print(f"absence integration   : {world['state']['absence_integration']}")
    print(f"world formation density: {world['formation_density']}")
    print(f"report                : {out['markdown']}")
    print("note: this is an observable internal structural world; it is NOT a "
          "subjective world, NOT qualia, and NOT proof of experience.")


if __name__ == "__main__":
    main()
