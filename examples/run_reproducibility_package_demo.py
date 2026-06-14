#!/usr/bin/env python3
"""Reproducibility package demo: artifact index, checksums, missing list.

    python examples/run_reproducibility_package_demo.py --state-dir .solaris_ai_nn_pilot1/test_repro_package

Builds a reproducibility package from a small mock artifact set: it indexes
large logs (rather than copying them), writes a checksum manifest for the
small artifacts, lists missing artifacts, and includes no secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
if os.path.isdir(_SRC):
    sys.path.insert(0, os.path.abspath(_SRC))

from solaris_ai_nn.post_pilot import PilotArtifactLoader, ReproducibilityPackager


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reproducibility package demo")
    parser.add_argument("--state-dir", type=str,
                        default=".solaris_ai_nn_pilot1/test_repro_package")
    args = parser.parse_args()

    base = os.path.join(args.state_dir, "pilot1")
    state = os.path.join(args.state_dir, "state")
    os.makedirs(base, exist_ok=True)
    os.makedirs(state, exist_ok=True)
    with open(os.path.join(base, "observability.jsonl"), "w",
              encoding="utf-8") as fh:
        for i in range(20):
            fh.write(json.dumps({"kind": "metrics", "payload": {"i": i}}) + "\n")
    with open(os.path.join(base, "PILOT_REPORT.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"sections": {"config": {"seed": 7, "is_simulated": True,
                                           "enabled_modules": ["bridge"],
                                           "time_label": "SIMULATED-TIME"}}},
                  fh)

    artifacts = PilotArtifactLoader(base, state).load()
    packager = ReproducibilityPackager(base_dir=base)
    pkg, paths = packager.build_and_write(artifacts)

    print("=== Reproducibility package ===")
    print(f"seed             : {pkg.seed}")
    print(f"time label       : {pkg.time_label} (simulated={pkg.is_simulated})")
    print(f"checksummed       : {sorted(pkg.checksum_manifest)}")
    print(f"indexed-only      : {pkg.indexed_only}")
    print(f"missing artifacts : {len(pkg.missing_artifacts)}")
    print(f"manifest          : {paths['manifest']}")
    print(f"checksums         : {paths['checksums']}")


if __name__ == "__main__":
    main()
