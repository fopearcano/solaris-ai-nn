#!/usr/bin/env python3
"""Desire formation demo: valence gradient -> push -> desire candidate -> report.

    python examples/run_desire_formation_demo.py --state-dir .solaris_ai_nn_desire/test_desire_formation

Feeds a fixture sensorium + perceptual metabolism into the desire-formation runtime,
which assesses valence, forms pushes and desire candidates, arbitrates safely, runs
allowed internal actions, and writes the report. Desire is operational pressure
toward internal actions, NOT emotion or human wanting.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.desire_formation import DesireFormationRuntime
from solaris_ai_nn.perceptual_metabolism import PerceptualMetabolismRuntime
from solaris_ai_nn.plural_sensorium import PluralSensoriumRuntime, fixture_feeder


def _feeder(base, mod, fn, n=12):
    path = os.path.join(base, f"{fn}.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": mod, "v": 0.6 + 0.3 * (i % 2),
                                 "ts": float(i)}) + "\n")
    return fixture_feeder(f"{fn}_feed", path, mod)


def main():
    parser = argparse.ArgumentParser(description="Desire formation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_desire/test_desire_formation")
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

    rt = DesireFormationRuntime(state_dir=base, sensorium=sensorium,
                                metabolism=met, max_ticks=3)
    rt.run_bounded()
    status = rt.desire_status()
    out = rt.write_artifacts()

    print("=== Desire formation demo ===")
    print(f"valence gradients     : {status['valence_gradient_count']} "
          f"(dominant {status['dominant_valence_direction']})")
    print(f"pushes                : {status['push_count']}")
    print(f"desire candidates     : {status['desire_candidate_count']} "
          f"(active {status['active_desire_count']})")
    print(f"internal actions      : {status['internal_action_count']} "
          f"(no-op {status['no_op_count']})")
    print(f"conflicts             : {status['desire_conflict_count']}")
    print(f"outcome success rate  : {status['desire_outcome_success_rate']}")
    print(f"report                : {out['markdown']}")
    print("note                  : desire candidates are operational pressures "
          "toward internal actions; they are not emotions, human wants, free "
          "will, or proof of agency.")


if __name__ == "__main__":
    main()
