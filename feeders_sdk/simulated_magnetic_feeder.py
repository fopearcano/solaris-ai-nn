#!/usr/bin/env python3
"""Simulated magnetic feeder -- safe magnetic-field envelopes (NOT a sensor).

OUTSIDE Solaris. Generates simulated magnetic *field* envelopes with a slow
baseline drift, an occasional anomaly, and jitter. A fixture for the feeder
contract; NOT a real sensor. Stdlib only.

    python feeders_sdk/simulated_magnetic_feeder.py --out out/magnetic.jsonl --count 20 --seed 7
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
        drift = 0.0 if i < count // 2 else 0.4
        anomaly = 1.2 if (count // 2) <= i < (count // 2 + 2) else 0.0
        out.append({
            "event_id": f"FSE_{uuid.uuid4().hex[:10]}",
            "feeder_id": "simulated_magnetic_feeder", "source_id": "sim_magnetic",
            "source_kind": "fixture_replay", "modality": "magnetic",
            "timestamp": float(i),
            "features": {"field": round(0.2 + drift + anomaly
                                        + 0.03 * rng.random(), 4),
                         "drift": round(drift, 4), "anomaly": round(anomaly, 4)},
            "annotation": None, "annotation_status": "none",
            "provenance": {"source_id": "sim_magnetic",
                           "feeder_id": "simulated_magnetic_feeder",
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
    parser = argparse.ArgumentParser(description="Simulated magnetic feeder")
    parser.add_argument("--out", required=True)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    events = generate(args.count, args.seed)
    with open(args.out, "a", encoding="utf-8") as fh:
        for env in events:
            fh.write(json.dumps(env) + "\n")
    print(f"simulated_magnetic_feeder wrote {len(events)} envelope(s) to "
          f"{args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
