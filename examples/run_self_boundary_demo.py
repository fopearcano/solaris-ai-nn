#!/usr/bin/env python3
"""Self-boundary demo: receptor body schema, source attribution, report.

    python examples/run_self_boundary_demo.py --state-dir .solaris_ai_nn_self_boundary/test_self_boundary

Feeds a fixture sensorium into the self-boundary runtime, which builds a receptor
body schema, attributes external sources, classifies internal/external, and writes
the report. Self-boundary is operational, NOT subjective selfhood.
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
from solaris_ai_nn.self_boundary import SelfBoundaryRuntime


def _feeder(base, mod, fn, n=12):
    path = os.path.join(base, f"{fn}.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        for i in range(n):
            fh.write(json.dumps({"modality": mod, "v": 0.6 + 0.3 * (i % 2),
                                 "ts": float(i)}) + "\n")
    return fixture_feeder(f"{fn}_feed", path, mod)


def main():
    parser = argparse.ArgumentParser(description="Self-boundary demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_self_boundary/test_self_boundary")
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

    sb = SelfBoundaryRuntime(
        state_dir=base, sensorium=sensorium, metabolism=met,
        feeder_monitor_snapshot={"feeders": [{"feeder_id": "rf_feed"},
                                             {"feeder_id": "vib_feed"}]},
        max_ticks=3)
    sb.run_bounded()
    status = sb.self_boundary_status()
    out = sb.write_artifacts()

    print("=== Self-boundary demo ===")
    print(f"receptor body parts   : {status['receptor_body_schema_count']} "
          f"(stability {status['body_schema_stability']})")
    print(f"boundary events       : {status['boundary_event_count']} "
          f"(confidence {status['boundary_confidence_score']})")
    print(f"ownership attributions: {status['ownership_attribution_count']}")
    print(f"source attribution unc: "
          f"{status['source_attribution_uncertainty_score']}")
    print(f"boundary tensions     : {status['boundary_tension_count']}")
    print(f"report                : {out['markdown']}")
    print("note                  : self-boundary is operational boundary "
          "tracking between internal state, receptor body, external flux, "
          "memory, prediction, and simulation; it is not a claim of "
          "self-awareness or personhood.")


if __name__ == "__main__":
    main()
