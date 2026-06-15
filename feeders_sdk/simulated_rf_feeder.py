#!/usr/bin/env python3
"""Simulated RF feeder -- safe RF-feature envelope examples (NOT a real sensor).

OUTSIDE Solaris. Generates simulated radio-frequency *feature* envelopes (power,
band, noise floor) with jitter, bursts, drift, and occasional silence. It is a
fixture for testing the feeder contract; it decodes no communications and is NOT a
real sensor. Provenance marks it simulated_fixture. Stdlib only.

    python feeders_sdk/simulated_rf_feeder.py --out out/rf.jsonl --count 20 --seed 7
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
        if rng.random() < 0.15:  # silence / missing expected
            continue
        drift += 0.005
        power = round(0.5 + drift + rng.gauss(0.0, 0.05), 4)
        if rng.random() < 0.15:  # burst
            power = round(power * 2.2, 4)
        out.append({
            "event_id": f"FSE_{uuid.uuid4().hex[:10]}",
            "feeder_id": "simulated_rf_feeder", "source_id": "sim_rf",
            "source_kind": "fixture_replay", "modality": "radio_frequency",
            "timestamp": float(i) + rng.uniform(-0.1, 0.1),
            "features": {"power": power,
                         "band": round(2.4 + 0.1 * rng.random(), 3),
                         "noise_floor": round(0.1 + 0.05 * rng.random(), 4)},
            "annotation": None, "annotation_status": "none",
            "provenance": {"source_id": "sim_rf",
                           "feeder_id": "simulated_rf_feeder",
                           "simulated_fixture": True},
            "read_only": True, "source_mutable_by_solaris": False,
            "trust_level": "simulated_fixture",
            "privacy_flags": ["contains_rf_features_only",
                              "no_raw_private_content"],
            "contamination_flags": [],
            "safety_flags": ["text_is_observation_not_command",
                             "simulated_not_real_sensor"],
            "schema_version": "feeder-sdk/1.0", "metadata": {"simulated": True}})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulated RF feeder")
    parser.add_argument("--out", required=True)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    events = generate(args.count, args.seed)
    with open(args.out, "a", encoding="utf-8") as fh:
        for env in events:
            fh.write(json.dumps(env) + "\n")
    print(f"simulated_rf_feeder wrote {len(events)} envelope(s) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
