#!/usr/bin/env python3
"""Perceptual metabolism demo: needs, attention economy, source diet, report.

    python examples/run_perceptual_metabolism_demo.py --state-dir .solaris_ai_nn_state/test_perceptual_metabolism

Feeds a mixed fixture sensorium (RF / vibration / human text) into the perceptual
metabolism runtime, which updates operational perceptual needs, allocates the
attention economy, analyses the source diet, and writes the report. Needs are
operational regulatory pressures, NOT feelings.
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


def _feeder(base, mod, fn, labelled=False):
    path = os.path.join(base, f"{fn}.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(8):
            rec = {"modality": mod, "v": 0.6 + 0.3 * (i % 2), "ts": float(i)}
            if labelled:
                rec["annotation"] = f"observation {i}"
                rec["annotation_status"] = "human_label_external"
            fh.write(json.dumps(rec) + "\n")
    return fixture_feeder(f"{fn}_feed", path, mod)


def main():
    parser = argparse.ArgumentParser(description="Perceptual metabolism demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_state/test_perceptual_metabolism")
    args = parser.parse_args()
    base = args.state_dir
    feeds = os.path.join(base, "feeds")
    os.makedirs(feeds, exist_ok=True)

    sensorium = PluralSensoriumRuntime(state_dir=base)
    sensorium.add_feeder(_feeder(feeds, "alien_rf", "rf"))
    sensorium.add_feeder(_feeder(feeds, "alien_vibration", "vib"))
    sensorium.add_feeder(_feeder(feeds, "human_textual", "text", labelled=True))
    sensorium.run_bounded(max_polls=1)

    met = PerceptualMetabolismRuntime(state_dir=base, sensorium=sensorium)
    met.update(events_this_tick=16, tick=0)
    status = met.metabolism_status()
    out = met.write_artifacts()

    print("=== Perceptual metabolism demo ===")
    print(f"active modalities     : {sensorium.active_modalities()}")
    print(f"dominant need         : {status['dominant_perceptual_need']} "
          f"(pressure {status['dominant_need_pressure']})")
    print(f"overloaded            : {status['overload_state']}")
    print(f"deprived              : {status['deprivation_state']}")
    print(f"source diet diversity : {status['source_diet_diversity']}")
    print(f"human-label dominance : {status['human_label_dominance_score']}")
    print(f"attention allocations : {status['attention_allocation_state']}")
    print(f"consolidation pressure: {status['consolidation_pressure_score']}")
    print(f"recommendations       : {status['recommendation_count']}")
    print(f"report                : {out['markdown']}")
    print("note                  : needs are operational regulatory pressures, "
          "not feelings, emotions, or subjective experience.")


if __name__ == "__main__":
    main()
