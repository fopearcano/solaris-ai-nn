#!/usr/bin/env python3
"""Cross-modal sensorium demo: RF burst -> vibration; thermal -> machine rhythm.

    python examples/run_cross_modal_sensorium_demo.py --state-dir .solaris_ai_nn_state/test_cross_modal_sensorium

Feeds interleaved RF-then-vibration and thermal-then-machine-rhythm streams and
shows cross-modal relations forming (followed_by / coincides_with) without
forcing any human object ontology.
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
    parser = argparse.ArgumentParser(description="Cross-modal sensorium demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_cross_modal_sensorium")
    args = parser.parse_args()
    base = args.state_dir
    feeds = os.path.join(base, "feeds")
    os.makedirs(feeds, exist_ok=True)

    # RF bursts at t=0,2,4,...; vibration follows ~0.3s later each time.
    rf = os.path.join(feeds, "rf.jsonl")
    vib = os.path.join(feeds, "vib.jsonl")
    thermal = os.path.join(feeds, "thermal.jsonl")
    machine = os.path.join(feeds, "machine.jsonl")
    with open(rf, "w") as f, open(vib, "w") as g, \
            open(thermal, "w") as h, open(machine, "w") as k:
        for i in range(6):
            t = float(i * 2)
            f.write(json.dumps({"modality": "alien_rf", "power": 0.9,
                                "ts": t}) + "\n")
            g.write(json.dumps({"modality": "alien_vibration", "amp": 0.7,
                                "ts": t + 0.3}) + "\n")
            h.write(json.dumps({"modality": "alien_thermal", "grad": 0.5,
                                "ts": t + 0.6}) + "\n")
            k.write(json.dumps({"modality": "machine_rhythm", "load": 0.4,
                                "ts": t + 0.9}) + "\n")

    rt = PluralSensoriumRuntime(state_dir=base)
    rt.add_feeder(fixture_feeder("rf_feed", rf, "alien_rf"))
    rt.add_feeder(fixture_feeder("vib_feed", vib, "alien_vibration"))
    rt.add_feeder(fixture_feeder("thermal_feed", thermal, "alien_thermal"))
    rt.add_feeder(fixture_feeder("machine_feed", machine, "machine_rhythm"))
    rt.run_bounded(max_polls=1)

    relations = rt.cross_modal.all_relations()
    out = PluralSensoriumReportBuilder(rt).write()
    print("=== Cross-modal sensorium demo ===")
    print(f"cross-modal relations : {len(relations)}")
    for rel in relations[:6]:
        print(f"  {rel.modality_a} -{rel.relation_type}-> {rel.modality_b} "
              f"(lag {rel.lag:.2f}s, support {rel.support})")
    print(f"report                : {out['markdown']}")
    print("note                  : relations stored without human object "
          "ontology; modality-native structure preserved.")


if __name__ == "__main__":
    main()
