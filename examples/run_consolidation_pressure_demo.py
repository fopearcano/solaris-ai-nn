#!/usr/bin/env python3
"""Consolidation pressure demo: many weak structures -> digest, don't ingest.

    python examples/run_consolidation_pressure_demo.py --state-dir .solaris_ai_nn_state/test_consolidation_pressure

Drives a sensorium until it accumulates many invariants / proto-symbols and some
fatigue, then shows the consolidation-pressure estimator recommending consolidation
(and which latent-replay kinds would help). Nothing sleeps forever and no evidence
is erased.
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
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def main():
    parser = argparse.ArgumentParser(description="Consolidation pressure demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_consolidation_pressure")
    args = parser.parse_args()
    base = args.state_dir
    feeds = os.path.join(base, "feeds")
    os.makedirs(feeds, exist_ok=True)

    sensorium = PluralSensoriumRuntime(state_dir=base)
    # Several modalities with sustained, varied activity -> many structures.
    for mod, fn in (("alien_rf", "rf"), ("alien_echo", "echo"),
                    ("vibration", "vib"), ("magnetic", "mag")):
        path = os.path.join(feeds, f"{fn}.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for i in range(16):
                fh.write(json.dumps({"modality": mod,
                                     "v": 0.5 + 0.4 * (i % 2),
                                     "ts": float(i)}) + "\n")
        sensorium.add_feeder(fixture_feeder(f"{fn}_feed", path, mod))
    sensorium.run_bounded(max_polls=1)
    # Induce some receptor fatigue to raise consolidation pressure.
    for r in sensorium.receptors.values():
        r.fatigue = 0.8

    met = PerceptualMetabolismRuntime(state_dir=base, sensorium=sensorium)
    met.update(events_this_tick=10, tick=0)
    cons = met._last.get("consolidation", {})

    print("=== Consolidation pressure demo ===")
    print(f"invariant candidates  : {len(sensorium.invariants.candidates)}")
    print(f"proto-symbols         : {len(sensorium.proto_symbol_candidates)}")
    print(f"consolidation pressure: {cons.get('pressure')}")
    print(f"recommendation        : {cons.get('recommendation')}")
    print(f"latent replay recs    : {met.latent_replay_recommendations()}")
    print("note                  : recommendation only; nothing sleeps forever "
          "and no evidence is erased.")


if __name__ == "__main__":
    main()
