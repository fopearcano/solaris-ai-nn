#!/usr/bin/env python3
"""Multimodal feeder demo -- combine the simulated feeders into one stream.

OUTSIDE Solaris. Generates a single JSONL stream mixing simulated RF, echo,
vibration, magnetic, and thermal envelopes (with jitter / silence / drift / noise),
plus an RF->vibration cross-modal coupling. A fixture for the feeder contract and
the Live Field; NOT a real sensor. Stdlib only.

    python feeders_sdk/multimodal_feeder_demo.py --out out/multimodal.jsonl --count 20 --seed 7
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import simulated_echo_feeder as echo  # noqa: E402
import simulated_magnetic_feeder as mag  # noqa: E402
import simulated_rf_feeder as rf  # noqa: E402
import simulated_thermal_feeder as thermal  # noqa: E402
import simulated_vibration_feeder as vib  # noqa: E402


def generate(count: int, seed: int) -> list:
    events = []
    events += rf.generate(count, seed)
    events += echo.generate(count, seed + 1)
    events += vib.generate(count, seed + 2)
    events += mag.generate(count, seed + 3)
    events += thermal.generate(count, seed + 4)
    events.sort(key=lambda e: e["timestamp"])
    return events


def main() -> int:
    parser = argparse.ArgumentParser(description="Multimodal feeder demo")
    parser.add_argument("--out", required=True)
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    events = generate(args.count, args.seed)
    with open(args.out, "w", encoding="utf-8") as fh:
        for env in events:
            fh.write(json.dumps(env) + "\n")
    modalities = sorted({e["modality"] for e in events})
    print(f"multimodal_feeder_demo wrote {len(events)} envelope(s) "
          f"({modalities}) to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
