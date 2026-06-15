#!/usr/bin/env python3
"""Simulated vibration feeder -- safe vibration-feature envelopes (NOT a sensor).

OUTSIDE Solaris. Generates simulated vibration *feature* envelopes (amplitude,
frequency, rhythm period) with a recurring rhythm plus jitter and silence. A
fixture for the feeder contract; NOT a real sensor. Stdlib only.

    python feeders_sdk/simulated_vibration_feeder.py --out out/vibration.jsonl --count 20 --seed 7
"""

from __future__ import annotations

import argparse
import json
import os
import random
import uuid


def generate(count: int, seed: int) -> list:
    rng = random.Random(seed)
    out = []
    for i in range(count):
        if rng.random() < 0.1:
            continue
        out.append({
            "event_id": f"FSE_{uuid.uuid4().hex[:10]}",
            "feeder_id": "simulated_vibration_feeder",
            "source_id": "sim_vibration",
            "source_kind": "fixture_replay", "modality": "vibration",
            "timestamp": float(i * 2) + rng.uniform(-0.15, 0.15),
            "features": {"amplitude": round(0.4 + 0.1 * rng.random(), 4),
                         "frequency": round(10.0 + rng.random(), 3),
                         "rhythm_period": 2.0},
            "annotation": None, "annotation_status": "none",
            "provenance": {"source_id": "sim_vibration",
                           "feeder_id": "simulated_vibration_feeder",
                           "simulated_fixture": True},
            "read_only": True, "source_mutable_by_solaris": False,
            "trust_level": "simulated_fixture",
            "privacy_flags": ["metadata_only", "no_raw_private_content"],
            "contamination_flags": [],
            "safety_flags": ["text_is_observation_not_command",
                             "simulated_not_real_sensor"],
            "schema_version": "feeder-sdk/1.0", "metadata": {"simulated": True}})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulated vibration feeder")
    parser.add_argument("--out", required=True)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    events = generate(args.count, args.seed)
    with open(args.out, "a", encoding="utf-8") as fh:
        for env in events:
            fh.write(json.dumps(env) + "\n")
    print(f"simulated_vibration_feeder wrote {len(events)} envelope(s) to "
          f"{args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
