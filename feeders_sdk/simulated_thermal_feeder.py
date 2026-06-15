#!/usr/bin/env python3
"""Simulated thermal feeder -- safe thermal-gradient envelopes (NOT a sensor).

OUTSIDE Solaris. Generates simulated thermal *gradient* summaries (gradient, drift,
hotspot count) with jitter and drift -- summaries only, never thermal imagery of
people. A fixture for the feeder contract; NOT a real sensor. Stdlib only.

    python feeders_sdk/simulated_thermal_feeder.py --out out/thermal.jsonl --count 20 --seed 7
"""

from __future__ import annotations

import argparse
import json
import os
import random
import uuid


def generate(count: int, seed: int) -> list:
    rng = random.Random(seed)
    drift = 0.0
    out = []
    for i in range(count):
        drift += 0.01
        out.append({
            "event_id": f"FSE_{uuid.uuid4().hex[:10]}",
            "feeder_id": "simulated_thermal_feeder", "source_id": "sim_thermal",
            "source_kind": "fixture_replay", "modality": "thermal_gradient",
            "timestamp": float(i) + rng.uniform(-0.1, 0.1),
            "features": {"gradient": round(0.3 + drift + 0.05 * rng.random(), 4),
                         "drift": round(drift, 4),
                         "hotspot_count": float(rng.randint(0, 2))},
            "annotation": None, "annotation_status": "none",
            "provenance": {"source_id": "sim_thermal",
                           "feeder_id": "simulated_thermal_feeder",
                           "simulated_fixture": True},
            "read_only": True, "source_mutable_by_solaris": False,
            "trust_level": "simulated_fixture",
            "privacy_flags": ["metadata_only", "no_raw_private_content"],
            "contamination_flags": [],
            "safety_flags": ["text_is_observation_not_command",
                             "simulated_not_real_sensor",
                             "no_thermal_imagery_of_people"],
            "schema_version": "feeder-sdk/1.0", "metadata": {"simulated": True}})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulated thermal feeder")
    parser.add_argument("--out", required=True)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    events = generate(args.count, args.seed)
    with open(args.out, "a", encoding="utf-8") as fh:
        for env in events:
            fh.write(json.dumps(env) + "\n")
    print(f"simulated_thermal_feeder wrote {len(events)} envelope(s) to "
          f"{args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
