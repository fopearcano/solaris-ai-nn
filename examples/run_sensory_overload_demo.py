#!/usr/bin/env python3
"""Sensory overload demo: a noisy/bursty source triggers internal throttling.

    python examples/run_sensory_overload_demo.py --state-dir .solaris_ai_nn_state/test_sensory_overload

Drives a high per-tick event count and a noisy source, shows the overload detector
firing with throttling recommendations, and confirms that no evidence is deleted
and no source is modified.
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
    parser = argparse.ArgumentParser(description="Sensory overload demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_sensory_overload")
    args = parser.parse_args()
    base = args.state_dir
    os.makedirs(base, exist_ok=True)

    # A noisy, bursty RF source.
    path = os.path.join(base, "rf.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(30):
            power = 2.5 if i % 3 == 0 else 0.6  # bursts
            fh.write(json.dumps({"modality": "alien_rf", "power": power,
                                 "ts": float(i)}) + "\n")
    sensorium = PluralSensoriumRuntime(state_dir=base)
    sensorium.add_feeder(fixture_feeder("rf_feed", path, "alien_rf"))
    sensorium.run_bounded(max_polls=1)
    before_events = sum(r.event_count for r in sensorium.receptors.values())

    met = PerceptualMetabolismRuntime(state_dir=base, sensorium=sensorium,
                                      overload_threshold=20)
    met.update(events_this_tick=200, tick=0)  # event flood
    after_events = sum(r.event_count for r in sensorium.receptors.values())

    print("=== Sensory overload demo ===")
    print(f"overloaded            : {met.overload.state.overloaded}")
    for ev in met.overload.state.events:
        print(f"  {ev.kind}: responses={ev.responses}")
    print(f"evidence preserved    : {after_events == before_events} "
          f"(events unchanged: {before_events})")
    print("note                  : overload throttles internal processing only; "
          "no evidence is deleted and no source is modified.")


if __name__ == "__main__":
    main()
