#!/usr/bin/env python3
"""Sensory deprivation demo: source silence -> absence pressure -> stimulus.

    python examples/run_sensory_deprivation_demo.py --state-dir .solaris_ai_nn_state/test_sensory_deprivation

Runs a brief RF source then lets it go silent, registers an expected signal that
becomes overdue, and shows the deprivation detector treating silence as a
first-class stimulus (absence pressure, silence-as-stimulus responses).
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
    parser = argparse.ArgumentParser(description="Sensory deprivation demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_sensory_deprivation")
    args = parser.parse_args()
    base = args.state_dir
    os.makedirs(base, exist_ok=True)

    # A short RF burst that then stops (the source goes silent).
    path = os.path.join(base, "rf.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(4):
            fh.write(json.dumps({"modality": "alien_rf", "power": 0.6,
                                 "ts": float(i)}) + "\n")
    sensorium = PluralSensoriumRuntime(state_dir=base)
    sensorium.add_feeder(fixture_feeder("rf_feed", path, "alien_rf"))
    sensorium.run_bounded(max_polls=1)
    # Make the receptor look silent for a while, and the field absence-heavy.
    for r in sensorium.receptors.values():
        r.silence_duration = 5.0
        r.recent_novelty = 0.0
    sensorium.sensory_field.pressures["absence"].value = 0.6
    sensorium.sensory_field.pressures["novelty"].value = 0.0

    met = PerceptualMetabolismRuntime(state_dir=base, sensorium=sensorium)
    met.update(events_this_tick=0, tick=0)

    print("=== Sensory deprivation demo ===")
    print(f"deprived              : {met.deprivation.state.deprived}")
    for ev in met.deprivation.state.events:
        print(f"  {ev.kind}: responses={ev.responses}")
    absence_need = met.needs.get("absence_resolution_need")
    print(f"absence resolution need pressure: {absence_need.pressure:.2f}")
    print("note                  : silence is stimulus; absence can become "
          "world-model structure.")


if __name__ == "__main__":
    main()
