#!/usr/bin/env python3
"""Sensorium grounding demo: invariant -> proto-symbol, world node, hypothesis.

    python examples/run_sensorium_grounding_demo.py --state-dir .solaris_ai_nn_state/test_sensorium_grounding

Drives a recurring RF burst until it becomes a stable invariant, which is
promoted to a modality-grounded proto-symbol candidate, a world-model node, and a
seeded hypothesis -- all without any human semantic label.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder
from solaris_ai_nn.plural_sensorium.reports import PluralSensoriumReportBuilder


def main():
    parser = argparse.ArgumentParser(description="Sensorium grounding demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_sensorium_grounding")
    args = parser.parse_args()
    base = args.state_dir
    feeds = os.path.join(base, "feeds")
    os.makedirs(feeds, exist_ok=True)

    rf = os.path.join(feeds, "rf.jsonl")
    with open(rf, "w", encoding="utf-8") as fh:
        for i in range(10):
            # A stable RF burst, repeated -> a recurring invariant.
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.7,
                                 "ts": float(i)}) + "\n")

    rt = PluralSensoriumRuntime(state_dir=base)
    rt.add_feeder(fixture_feeder("rf_feed", rf, "alien_rf"))
    rt.run_bounded(max_polls=1)
    out = PluralSensoriumReportBuilder(rt).write()

    print("=== Sensorium grounding demo ===")
    print(f"invariant candidates  : {len(rt.invariants.candidates)}")
    protos = rt.proto_symbol_candidates
    print(f"proto-symbol candidates: {len(protos)}")
    for p in protos[:4]:
        print(f"  {p['symbol_type']} <- {p['modality']} "
              f"(grounding {p['grounding_quality']}, "
              f"human_label_contaminated={p['human_label_contaminated']})")
    wm = [s for s in rt.world_model_structures
          if s["kind"] in ("invariant_candidate", "modality_source")]
    print(f"world-model structures: {len(wm)}")
    print(f"hypotheses seeded     : {len(rt.hypotheses)}")
    print(f"report                : {out['markdown']}")
    print("note                  : grounding rests on feature patterns + "
          "provenance; no human semantic label is required.")


if __name__ == "__main__":
    main()
